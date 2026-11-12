var form = document.getElementById('register-form');
var nameInput = document.getElementById('name');
var emailInput = document.getElementById('email');
var passwordInput = document.getElementById('password');
var confirmInput = document.getElementById('confirm');
var strengthBar = document.getElementById('strength-bar');
var strengthLabel = document.getElementById('strength-label');

function setError(input, errorId, message) {
  input.classList.toggle('invalid', Boolean(message));
  document.getElementById(errorId).textContent = message || '';
}

function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

// Правила пароля — такие же, как в file.py (там проверка главная, эта — для удобства)
function checkPassword(value) {
  if (value.length < 8) return 'Пароль должен быть не короче 8 символов';
  if (value.length > 64) return 'Пароль слишком длинный (не больше 64 символов)';
  if (!/[a-zA-Zа-яА-ЯёЁ]/.test(value)) return 'В пароле должна быть хотя бы одна буква';
  if (!/[0-9]/.test(value)) return 'В пароле должна быть хотя бы одна цифра';
  return '';
}

// Индикатор надёжности пароля
passwordInput.addEventListener('input', function () {
  var value = passwordInput.value;
  var score = 0;
  if (value.length >= 8) score++;
  if (value.length >= 12) score++;
  if (/[0-9]/.test(value) && /[a-zA-Zа-яА-ЯёЁ]/.test(value)) score++;

  var labels = ['Слабый пароль', 'Средний пароль', 'Надёжный пароль', 'Отличный пароль'];
  var colors = ['#ffa8d5', '#ff69b4', '#e0218a', '#b8106f'];

  strengthBar.style.width = value ? ((score + 1) * 25) + '%' : '0';
  strengthBar.style.background = colors[score];
  strengthLabel.textContent = value ? labels[score] : '';
});

form.addEventListener('submit', function (e) {

  var name = nameInput.value.trim();
  var email = emailInput.value.trim();
  var password = passwordInput.value;
  var confirm = confirmInput.value;
  var ok = true;

  if (name.length < 2) {
    setError(nameInput, 'name-error', 'Введите имя (минимум 2 символа)');
    ok = false;
  } else {
    setError(nameInput, 'name-error', '');
  }

  if (!isValidEmail(email)) {
    setError(emailInput, 'email-error', 'Некорректный email');
    ok = false;
  } else {
    setError(emailInput, 'email-error', '');
  }

  var passwordProblem = checkPassword(password);
  if (passwordProblem) {
    setError(passwordInput, 'password-error', passwordProblem);
    ok = false;
  } else {
    setError(passwordInput, 'password-error', '');
  }

  if (!confirm || confirm !== password) {
    setError(confirmInput, 'confirm-error', 'Пароли не совпадают');
    ok = false;
  } else {
    setError(confirmInput, 'confirm-error', '');
  }

  // Ошибки в форме — остаёмся на странице и ничего не отправляем
  if (!ok) {
    e.preventDefault();
    return;
  }

  // Всё верно: форма уходит на сервер (POST /register)
  var btn = document.getElementById('submit-btn');
  btn.disabled = true;
  btn.textContent = 'Создаём аккаунт... ✨';
}); 