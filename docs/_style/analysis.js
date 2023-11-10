var sectionColors = ['#37c', '#aa0', '#c50']
var borderColors = ['#008', '#660', '#820']
var textColors = ['#ccf', '#330', '#500']

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
function composeSprintBacklog() {
    let productBacklog = document.getElementById('product-backlog')
    let productUSs = productBacklog.children
    let sprintBacklog = document.getElementById('sprint-backlog')

    for (let n = 0; n < productUSs.length; n++) {
        let assignmentNode = productUSs[n].getElementsByClassName('assignment')[0]
        for (let s = 2; s <= 7; s++) {
            if (assignmentNode.getElementsByClassName('state-'+ s).length > 0) {
                sprintBacklog.appendChild(productUSs[n].cloneNode(true))
                break
            }
        }
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
        menuItems[n].style.marginRight = (n == sectionNumber) ? '-.5em' : '0'
        menuItems[n].style.borderRadius = (n == sectionNumber) ? '0' : '2em 0 0 2em'
    }
}