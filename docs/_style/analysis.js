var sectionColors = ['#37c', '#27bc23', '#aa0', '#c50']
var borderColors = ['#008', '#1b760d', '#660', '#820']
var textColors = ['#ccf', '#145e09', '#330', '#500']

function composeBacklogs() {
    colorSections()
    composeDoneBacklog()
    orderProductBacklog()
    composeSprintBacklog()
}

function colorSections() {
    let menuItems = document.getElementById('menu').firstChild.children
    let contentSections = document.getElementById('content').children

    for (let n = 0; n < menuItems.length; n++) {
        contentSections[n].style.background = sectionColors[n]
        contentSections[n].style.border = '.5em solid ' + borderColors[n]
        contentSections[n].style.borderTop = 'none'
        contentSections[n].style.borderRight = 'none'
        menuItems[n].style.background = sectionColors[n]
        menuItems[n].style.color = textColors[n]
        menuItems[n].style.border = '.2em solid ' + sectionColors[n]
    }
}
function orderProductBacklog() {
    let productBacklog = document.getElementById('product-backlog')
    let USNum = productBacklog.children.length
    let toBeRemovedNodes = []

    let priorityOrder = ['medium', 'low']
    for (let o = 0; o < priorityOrder.length; o++) {
        for (let n = 0; n < USNum; n++) {
            let USNode = productBacklog.children[n]
            let priority = USNode.getElementsByTagName('header')[0].children[2].classList[1]
            if (priority === priorityOrder[o]) {
                productBacklog.appendChild(USNode.cloneNode(true))
                toBeRemovedNodes.push(n)
            }
        }
    }
    removeNodesFromBacklog(toBeRemovedNodes, productBacklog)
}
function composeDoneBacklog() {
    let productBacklog = document.getElementById('product-backlog')
    let productUSs = productBacklog.children
    let doneBacklog = document.getElementById('done-backlog')
    let toBeRemovedNodes = []

    for (let n = 0; n < productUSs.length; n++) {
        let assignmentNode = productUSs[n].getElementsByClassName('assignment')[0]
        if (assignmentNode.getElementsByClassName('state-8').length > 0) {
            doneBacklog.prepend(productUSs[n].cloneNode(true))
            toBeRemovedNodes.push(n)
        }
    }
    removeNodesFromBacklog(toBeRemovedNodes, productBacklog)
}
function composeSprintBacklog() {
    let productBacklog = document.getElementById('product-backlog')
    let productUSs = productBacklog.children
    let sprintBacklog = document.getElementById('sprint-backlog')
    let toBeRemovedNodes = []

    for (let n = 0; n < productUSs.length; n++) {
        let assignmentNode = productUSs[n].getElementsByClassName('assignment')[0]
        for (let s = 2; s <= 7; s++) {
            if (assignmentNode.getElementsByClassName('state-'+ s).length > 0) {
                sprintBacklog.appendChild(productUSs[n].cloneNode(true))
                break
            }
        }
    }
    for (let n = 0; n < productUSs.length; n++) {
        let state = productUSs[n].getElementsByClassName('assignment')[0].getElementsByTagName('span')[0].classList[0]
        if (state === 'state-2' || state === 'state-4' || state === 'state-6') {
            toBeRemovedNodes.push(n)
        }
    }
    removeNodesFromBacklog(toBeRemovedNodes, productBacklog)
}
function removeNodesFromBacklog(toBeRemovedNodes, backlogElement) {
    let toBeRemovedNodesNum = toBeRemovedNodes.length
    toBeRemovedNodes = toBeRemovedNodes.sort(function(a, b) { return a - b; })
    for (let n = toBeRemovedNodesNum - 1; n >= 0; n--) {
        backlogElement.children[toBeRemovedNodes[n]].remove()
    }
}
function showSection(sectionNumber) {
    let menuItems = document.getElementById('menu').firstChild.children
    let contentSections = document.getElementById('content').children

    for (let n = 0; n < menuItems.length; n++) {
        contentSections[n].style.display = (n == sectionNumber) ? 'inline-block' : 'none'
        menuItems[n].style.color = (n == sectionNumber) ? textColors[n] : borderColors[n]
        menuItems[n].style.borderLeft = '.5em solid ' + ((n == sectionNumber) ? borderColors[n] : sectionColors[n])
        menuItems[n].style.borderRight = '.2em solid ' + sectionColors[n]
        menuItems[n].style.marginLeft = (n == sectionNumber) ? '-1em' : '0'
        menuItems[n].style.marginRight = (n == sectionNumber) ? '-.8em' : '0'
        menuItems[n].style.borderRadius = (n == sectionNumber) ? '0' : '2em 0 0 2em'
    }
}
function showLastSectionNotEmpty() {
    let sprintBacklog = document.getElementById('sprint-backlog')
    let productBacklog = document.getElementById('product-backlog')
    let doneBacklog = document.getElementById('done-backlog')

    if (sprintBacklog.children.length > 0) {
        showSection(3)
    } else if (productBacklog.children.length > 0) {
        showSection(2)
    } else if (doneBacklog.children.length > 0) {
        showSection(1)
    } else {
        showSection(0)
    }
}