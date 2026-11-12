(function () {
  // Приветствие в зависимости от времени суток
  var hours = new Date().getHours();
  var phrase = 'Добро пожаловать в';
  if (hours >= 5 && hours < 12) phrase = 'Доброе утро, красотка — ты в';
  else if (hours >= 12 && hours < 18) phrase = 'Добрый день, красотка — ты в';
  else if (hours >= 18 && hours < 23) phrase = 'Добрый вечер, красотка — ты в';

  document.getElementById('greeting').innerHTML = phrase + ' <span>БарбиЛенд</span>!';

  // Текущий год в подвале
  document.getElementById('year').textContent = new Date().getFullYear();
})();