Это необходимо сделать перед стартом на виндовс

wsl -d docker-desktop
sysctl -w vm.max_map_count=262144

Основные переменные программы
1 hostname
2 директория ci_cd с поддиректориями gitlab_ce, gitlab_ci, postgres
3 путь к текущей директории хранилища 1С
4 список пользователей гитлаб и 1С