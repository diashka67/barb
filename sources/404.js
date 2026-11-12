// Случайное «объяснение» произошедшего
var phrases = [
  'Эта страница пошла на шопинг и забыла вернуться 🛍️',
  'Мы обыскали весь Дримхаус, но её нигде нет 🏡',
  'Кажется, страница застряла в примерочной 👗',
  'Эта страница сейчас на маникюре 💅 и вернётся не скоро',
  'Здесь пусто. Даже блёсток не осталось ✨'
];

document.getElementById('phrase').textContent =
  phrases[Math.floor(Math.random() * phrases.length)];

// Кнопка «Назад»: в историю, а если её нет — на главную
document.getElementById('back-btn').addEventListener('click', function () {
  if (history.length > 1) {
    history.back();
  }
});