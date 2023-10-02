function CheckBoxVisibility(checkboxId, divId, isDivHide = true) {
    let checkbox = document.getElementById(checkboxId)
    let div = document.getElementById(divId)

    if (isDivHide)
        div.style.display = "none"

    checkbox.onchange = function() {
        div.style.display = checkbox.checked ? "block" : "none"
    }
}
