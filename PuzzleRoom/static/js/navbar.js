//C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\static\js\navbar.js
let menu = document.querySelector('#menu-icon');
let sidenavbar = document.querySelector('.side-navbar');
let content = document.querySelector('.content');
 
menu.onclick = () => {
    sidenavbar.classList.toggle('active');
    content.classList.toggle('active');
}