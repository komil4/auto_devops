#Использовать json
#Использовать 1commands

Перем г_ПутьКФайлуНастроек;

Функция СохранитьНастройкиИВыернутьSSH(СтрокаJSON) Экспорт

	Настройки = ПолучитьБазовыеНастройки();
	Парсер = Новый ПарсерJSON;
    Данные = Парсер.ПрочитатьJSON(СтрокаJSON,,,Истина);
    
	Если ТипЗнч(Данные) <> Тип("Соответствие") И ТипЗнч(Данные) <> Тип("Структура")  Тогда
		Возврат Настройки;
    КонецЕсли;

    Для каждого Объект Из Данные Цикл
		Настройки.Вставить(Объект.Ключ, Объект.Значение);
    КонецЦикла;

	Настройки = СгенерироватьSSH();
	Записать(Настройки);

	Возврат Парсер.ЗаписатьJSON(Настройки);

КонецФункции

Функция СгенерироватьSSH() Экспорт

	Данные = НастройкиСинхронизации.ПолучитьДанныеНастроек();
		
	Команда = Новый Команда;
	Команда.УстановитьСтрокуЗапуска("cd");
	Команда.Исполнить();
	Выводcd = Команда.ПолучитьВывод();
	Выводcd = СтрЗаменить(Выводcd, Символы.ПС, "");

	Если СтрНайти(Выводcd, ":\") > 0 Тогда
		Команда.УстановитьСтрокуЗапуска("rmdir /s /q ssh");
		Команда.УстановитьСтрокуЗапуска("mkdir ssh");
		Команда.Исполнить();
		Команда.УстановитьСтрокуЗапуска("ssh-keygen -b 2048 -t rsa -f " + Выводcd + "\ssh\id_rsa -q -N """"");
		Команда.Исполнить();
		Команда.УстановитьСтрокуЗапуска("type " + Выводcd + "\ssh\id_rsa.pub");
		Команда.Исполнить();
		Ключ = Команда.ПолучитьВывод();
	Иначе
		Команда.УстановитьСтрокуЗапуска("rm -rf ssh");
		Команда.УстановитьСтрокуЗапуска("mkdir ssh");
		Команда.УстановитьСтрокуЗапуска("whoami");
		Команда.Исполнить();
		Пользователь = Команда.ПолучитьВывод();
		Пользователь = СтрЗаменить(Пользователь, Символы.ПС, "");
		Команда.УстановитьСтрокуЗапуска("ssh-keygen -b 2048 -t rsa -f /" + Пользователь + "/.ssh/id_rsa -q -N """"");
		Команда.Исполнить();
		Команда.УстановитьСтрокуЗапуска("cat /" + Пользователь + "/.ssh/id_rsa.pub");
		Команда.Исполнить();
		Ключ = Команда.ПолучитьВывод();
	КонецЕсли;

	Ключ = СтрЗаменить(Ключ, Символы.ПС, "");
	Данные.Вставить("SSHkey", Ключ);
	Записать(Данные);

	Возврат Данные;

КонецФункции

Функция ПолучитьДанныеНастроек() Экспорт

    Настройки = ПолучитьБазовыеНастройки();

    Парсер = Новый ПарсерJSON;
    Данные = Парсер.ПрочитатьJSON(СодержимоеФайла(г_ПутьКФайлуНастроек),,,Истина);
    
	Если ТипЗнч(Данные) <> Тип("Соответствие") И ТипЗнч(Данные) <> Тип("Структура")  Тогда
		Возврат Настройки;
    КонецЕсли;

    Для каждого Объект Из Данные Цикл
		Настройки.Вставить(Объект.Ключ, Объект.Значение);
    КонецЦикла;

    Возврат Настройки;

КонецФункции

Функция СодержимоеФайла(п_ПутьКФайлу)
    
    Файл = Новый Файл(п_ПутьКФайлу);
    Если Не Файл.Существует() Тогда
        Содержимое = "[]";
    Иначе
        Текст = Новый ЧтениеТекста(п_ПутьКФайлу);
        Содержимое = Текст.Прочитать();
        Текст.Закрыть();
    КонецЕсли;
    
    Возврат Содержимое;
    
КонецФункции

Процедура Записать(Знач СтруктруаФайла) Экспорт

	Текст = Новый ЗаписьТекста(г_ПутьКФайлуНастроек);
	Запись = Новый ПарсерJSON;
	Текст.Записать(Запись.ЗаписатьJSON(СтруктруаФайла));
	Текст.Закрыть();

КонецПроцедуры

Функция ПолучитьБазовыеНастройки()
	Возврат Новый Структура("Dir, Url, User, Password, PrivateToken, SSHkey", "Директория", "Юрл", "Пользователь", "Пароль", "Токен", "SSHkey");
КонецФункции

г_ПутьКФайлуНастроек = "settings.json"