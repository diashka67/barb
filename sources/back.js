// Если человек нажал в браузере «Назад» — закрываем его сессию на сервере
// и отправляем на страницу входа. Подключается в <head> каждой страницы.
(function () {
  // Страница открыта кнопкой «Назад» или «Вперёд»?
  function openedByBackButton() {
    var nav = performance.getEntriesByType('navigation')[0];
    return Boolean(nav) && nav.type === 'back_forward';
  }

  function closeSession() {
    // Пока сервер отвечает, прячем страницу, чтобы не мелькал закрытый для гостей кабинет
    document.documentElement.style.visibility = 'hidden';

    fetch('/back', { method: 'POST' })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (data.logged_out) {
          location.replace('/login?loggedout=1');   // был вошёл — теперь нужно войти заново
        } else {
          document.documentElement.style.visibility = '';
        }
      })
      .catch(function () {
        document.documentElement.style.visibility = '';
      });
  }

  if (openedByBackButton()) closeSession();

  // Некоторые браузеры достают страницу из памяти без запроса — тогда сработает pageshow
  window.addEventListener('pageshow', function (e) {
    if (e.persisted) closeSession();
  });
})();
