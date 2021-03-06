import json
import socket
import datetime

import flask
import flask_login
import jinja2

import predict.cve
import predict.auth
import predict.github
import predict.plugins
import predict.conflict_resolution
import predict.models
import predict.labels


blueprint = flask.Blueprint("main", __name__)


@blueprint.route("/")
def base():
    if (
        flask.current_app.config["LOGIN_DISABLED"]
        or flask_login.current_user.is_authenticated
    ):
        return flask.redirect(flask.url_for("main.dashboard"))
    else:
        return flask.redirect(flask.url_for("main.login"))


@blueprint.route("/login", methods=["GET"])
def login():
    return flask.render_template("login.html", invalidLogin=False)


@blueprint.route("/login", methods=["POST"])
def login_post():
    username = flask.request.form["username"]
    password = flask.request.form["password"]

    authorized = predict.auth.authenticate_user(username, password)

    if authorized:
        return flask.redirect(
            flask.request.args.get("next", flask.url_for("main.dashboard"))
        )
    else:
        flask.flash("Unrecognized credentials! Please try again.")
        return flask.render_template("login.html")


@blueprint.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("main.base"))


@blueprint.route("/register", methods=["GET"])
def register():
    return flask.render_template(
        "register.html",
        user_regex=flask.current_app.config["USERNAME_REGEX"],
        password_regex=flask.current_app.config["PASSWORD_REGEX"],
    )


@blueprint.route("/register", methods=["POST"])
def register_post():
    username = flask.request.form["username"]
    password = flask.request.form["password"]
    confirm = flask.request.form["confirm"]

    if confirm != password:
        flask.flash("Passwords entered do not match! Please try again.")
        return flask.render_template("register.html")

    if not predict.auth.string_match(
        username, flask.current_app.config["USERNAME_REGEX"]
    ):
        flask.flash(flask.current_app.config["USERNAME_FEEDBACK"])
        return flask.render_template("register.html")

    if not predict.auth.string_match(
        password, flask.current_app.config["PASSWORD_REGEX"]
    ):
        flask.flash(flask.current_app.config["PASSWORD_FEEDBACK"])
        return flask.render_template("register.html")

    whitelist = flask.current_app.config.get("WHITELIST")
    if whitelist is not None and username not in whitelist:
        flask.flash(
            "Username not in the whitelist. Please register using your "
            + "whitelisted username."
        )
        return flask.render_template("register.html")

    created = predict.auth.create_user(username, password)

    if created:
        return flask.redirect(flask.url_for("main.login"))
    else:
        flask.flash("That username already exists! Please try again.")
        return flask.render_template("register.html")


@blueprint.route("/dashboard")
@flask_login.login_required
def dashboard():
    username = predict.auth.current_user()

    if flask.current_app.debug:
        predict.labels.create_test_labels(username)

    recent_labels = predict.labels.load_recent(username)

    plugins = predict.plugins.load_plugins()

    return flask.render_template(
        "dashboard.html",
        plugins=plugins,
        recent_labels=recent_labels,
        username=username,
    )


@blueprint.route("/resolution")
@flask_login.login_required
def conflict_resolution():

    entries = predict.db.Session.query(predict.models.Label).all()
    entries.sort(key=lambda entry: entry.username)
    entries.sort(key=lambda entry: entry.cve_id, reverse=True)

    currentUser = flask_login.current_user.get_id()
    blocks = predict.conflict_resolution.processEntries(entries, currentUser)

    return flask.render_template("conflict_resolution.html", blocks=blocks)


@blueprint.route("/cve/<cve_id>")
@flask_login.login_required
def cve_base(cve_id):
    cve_data = predict.cve.get_cve(cve_id)

    label_groups = predict.labels.load_labels(cve_id, predict.auth.current_user())

    if cve_data is not None and len(cve_data.get("git_links", [])) > 0:
        return flask.redirect(cve_data["git_links"][0][1])

    return flask.render_template(
        "sidebar_cve.html", cve_data=cve_data, label_groups=label_groups
    )


@blueprint.route("/cve/<cve_id>/info/<repo_user>/<repo_name>/<commit>")
@flask_login.login_required
def info_page(cve_id, repo_user, repo_name, commit):
    cve_data = predict.cve.get_cve(cve_id)

    label_groups = predict.labels.load_labels(cve_id, predict.auth.current_user())

    github_data = predict.github.get_commit_info(cve_id, repo_user, repo_name, commit)

    return flask.render_template(
        "info.html",
        cve_data=cve_data,
        label_groups=label_groups,
        github_data=github_data,
    )


@blueprint.route(
    "/cve/<cve_id>/blame/<repo_user>/<repo_name>/<commit>/<path:file_name>"
)
@flask_login.login_required
def blame_page(cve_id, repo_user, repo_name, commit, file_name):
    cve_data = predict.cve.get_cve(cve_id)

    label_groups = predict.labels.load_labels(cve_id, predict.auth.current_user())

    blame_data = predict.github.get_blame(
        cve_id, repo_user, repo_name, commit, file_name
    )

    diff_enabled = flask.request.args.get("diff") == "True"

    return flask.render_template(
        "blame.html",
        cve_data=cve_data,
        label_groups=label_groups,
        github_data=blame_data,
        diff_enabled=diff_enabled,
    )


@blueprint.route("/label", methods=["PUT"])
@flask_login.login_required
def label():
    cve_id = flask.request.json["cve_id"]
    username = predict.auth.current_user()
    labels = flask.request.json["labels"]
    edit_date = datetime.datetime.now()

    success = predict.labels.process_labels(cve_id, username, labels, edit_date)

    if success:
        return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
    else:
        return json.dumps({"success": False}), 400, {"ContentType": "application/json"}


@blueprint.route("/export", methods=["POST"])
def export():
    filter_ = flask.request.form["filter"]
    extra_data = flask.request.form.getlist("extra-data")  # Optional
    strategy = flask.request.form["strategy"]
    file_format = flask.request.form["file-format"]

    return predict.plugins.export(
        filter_=filter_,
        extra_data=extra_data,
        strategy=strategy,
        file_format=file_format,
    )


@blueprint.app_errorhandler(404)
def page_not_found(e):
    return flask.render_template("error.html", error=e)


def datetime_format(dt):
    delta = datetime.datetime.now() - dt

    threshold1 = datetime.timedelta(seconds=15)
    threshold2 = datetime.timedelta(seconds=60)
    threshold3 = datetime.timedelta(minutes=60)
    threshold4 = datetime.timedelta(hours=10)
    threshold5 = datetime.timedelta(days=1)

    if delta < threshold1:
        return "just now"
    elif delta < threshold2:
        return "a few seconds ago"
    elif delta < threshold3:
        return "%d minutes ago" % (delta.seconds // 60)
    elif delta < threshold4:
        return "%d hours ago" % (delta.seconds // 3600)
    elif delta < threshold5:
        timestring = dt.strftime("%I:%M %p").lstrip("0")
        return "yesterday at %s" % timestring
    else:
        datestring = dt.strftime("%b %d").replace(" 0", " ")
        timestring = dt.strftime("%I:%M %p").lstrip("0")
        return "{} at {}".format(datestring, timestring)


def svg(name, class_name=""):
    """Insert an svg"""
    with flask.current_app.open_resource("static/svg/{}.svg".format(name), "rt") as f:
        svg = f.read()

    svg = svg.replace("<svg ", '<svg class="icon {}" '.format(class_name))

    return jinja2.Markup(svg)
