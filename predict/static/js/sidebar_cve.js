function missing_commit_info_page(cve) {
    return function () {
        repo = document.getElementById("repo").value
        commit = document.getElementById("commit").value

        document.getElementById("missing-button").innerHTML = "<span class='spinner-border spinner-border-sm' role='status' aria-hidden='true'></span>"

        window.location.pathname = "cve/" + cve + "/info/" + repo + "/" + commit

        // Return false to avoid the real form submission
        return false
    }
}

function openLabels() {
    labelTab.classList.add("active")
    labelButton.classList.add("active")
    cveTab.classList.remove("active")
    cveButton.classList.remove("active")

    // Make sure all label textboxes are properly sized when we switch tabs
    labelInputs = document.querySelectorAll(".hidden-input")
    labelInputs.forEach((element) => {
        resize(element)()
    })
}

function openCVE() {
    cveTab.classList.add("active")
    cveButton.classList.add("active")
    labelTab.classList.remove("active")
    labelButton.classList.remove("active")
}

document.addEventListener("DOMContentLoaded", (event) => {
    // Set up the resize event listener
    labelInputs = document.querySelectorAll(".hidden-input")

    labelInputs.forEach((element) => {
        element.addEventListener("input", resize(element))
    })

    labelTab = document.getElementById("labels")
    cveTab = document.getElementById("cve-info")
    
    labelButton = document.getElementById("label-tab")
    cveButton = document.getElementById("cve-tab")

    labelButton.addEventListener("click", openLabels)
    cveButton.addEventListener("click", openCVE)
})

function resize(element) {
    return function() {
        hidden = document.getElementById("hidden-text")

        text = element.value
        if (text.length === 0) {
            text = element.placeholder
        }
        
        hidden.textContent = text
        element.style.width = hidden.offsetWidth + 4 + "px"
    }
}

function newHiddenInput(placeholder, value, className) {
    element = document.createElement("input")

    element.type = "text"
    element.value = value
    element.placeholder = placeholder
    element.className = className

    element.addEventListener("input", resize(element))
    element.addEventListener("input", labelsChanged)

    return element
}

function newSeparator(contents) {
    element = document.createElement("span")

    element.className = "hidden-input-sep"
    element.innerText = contents

    return element
}

function addLabel(button) {
    group = button.closest(".user-label-group")

    addLabelToGroup(group)

    labelsChanged()
}

function addLabelToGroup(group, fixFile, fixHash, introFile, introHash) {
    groupList = group.querySelector(".user-label-group-list")

    newLabel = document.createElement("li")
    newLabel.className = "list-group-item user-label"

    newFixFile = newHiddenInput("Fix File", fixFile, "hidden-input label-input fix-file")
    newFixSep = newSeparator("@")
    newFixHash = newHiddenInput("Fix Hash", fixHash, "hidden-input limited label-input fix-hash")
    newFixIntroSep = newSeparator("←")
    newIntroFile = newHiddenInput("Intro File", introFile, "hidden-input label-input intro-file")
    newIntroSep = newSeparator("@")
    newIntroHash = newHiddenInput("Intro Hash", introHash, "hidden-input limited label-input intro-hash")

    newRemoveLabel = document.createElement("a")
    newRemoveLabel.className = "remove-label"
    newRemoveLabel.onclick = function() { removeLabel(this) }

    newRemoveLabelIcon = document.createElement("i")
    newRemoveLabelIcon.className = "text-danger fas fa-times"

    newRemoveLabel.appendChild(newRemoveLabelIcon)

    newLabel.appendChild(newFixFile)
    newLabel.appendChild(newFixSep)
    newLabel.appendChild(newFixHash)
    newLabel.appendChild(newFixIntroSep)
    newLabel.appendChild(newIntroFile)
    newLabel.appendChild(newIntroSep)
    newLabel.appendChild(newIntroHash)
    newLabel.appendChild(newRemoveLabel)

    groupList.appendChild(newLabel)

    resize(newFixFile)()
    resize(newFixHash)()
    resize(newIntroFile)()
    resize(newIntroHash)()

    return newLabel
}

function removeLabel(button) {
    label = button.closest(".user-label")
    label.remove()

    labelsChanged()
}

function addGroupWithLabel() {
    group = addGroup(null, null)
    addLabelToGroup(group, null, null, null, null)
}

function addGroup(repoUser, repoName) {
    groups = document.getElementById("user-labels")

    card = document.createElement("div")
    card.className = "card user-label-group"

    cardHeader = document.createElement("div")
    cardHeader.className = "card-header user-label-group-header"

    newRepoUser = newHiddenInput("Repository Username", repoUser, "hidden-input repo-input repo-user")
    newRepoSep = newSeparator("/")
    newRepoName = newHiddenInput("Repository Name", repoName, "hidden-input repo-input repo-name")

    newRemoveGroup = document.createElement("a")
    newRemoveGroup.className = "remove-group"
    newRemoveGroup.onclick = function() { removeGroup(this) }

    newRemoveGroupIcon = document.createElement("i")
    newRemoveGroupIcon.className = "fas fa-times"

    newRemoveGroup.appendChild(newRemoveGroupIcon)

    cardHeader.appendChild(newRepoUser)
    cardHeader.appendChild(newRepoSep)
    cardHeader.appendChild(newRepoName)
    cardHeader.appendChild(newRemoveGroup)

    cardList = document.createElement("ul")
    cardList.className = "list-group list-group-flush user-label-group-list"

    addLabelButton = document.createElement("button")
    addLabelButton.className = "add-label"
    addLabelButton.onclick = function() { addLabel(this) }
    
    addLabelIcon = document.createElement("i")
    addLabelIcon.className = "fas fa-plus"
    
    addLabelText = document.createTextNode(" New Label")
    
    addLabelButton.appendChild(addLabelIcon)
    addLabelButton.appendChild(addLabelText)
    
    card.appendChild(cardHeader)
    card.appendChild(cardList)
    card.appendChild(addLabelButton)

    groups.append(card)

    resize(newRepoUser)()
    resize(newRepoName)()

    labelsChanged()

    return card
}

function removeGroup(button) {
    group = button.closest(".user-label-group")
    group.remove()

    labelsChanged()
}