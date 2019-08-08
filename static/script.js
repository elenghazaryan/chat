let clickCount = 0;

let p = document.getElementById("pElement");
window.param = p;

function clickHandler() {
    clickCount++;
    p.innerText = "Thanks for clicking " + clickCount;
}
