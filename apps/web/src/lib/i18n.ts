export const LOCALES = ["az", "en", "ru"] as const;
export type Locale = (typeof LOCALES)[number];

export const LOCALE_COOKIE = "yenimenzil-locale";

export function normalizeLocale(value?: string | null): Locale {
  const locale = value?.toLowerCase();
  return LOCALES.includes(locale as Locale) ? (locale as Locale) : "az";
}

const messages = {
  az: {
    "nav.sale": "Al", "nav.rent": "Kirayə", "nav.daily": "Günlük",
    "nav.newBuildings": "Yeni tikililər", "nav.house": "Həyət evi",
    "nav.villa": "Villa", "nav.land": "Torpaq", "nav.commercial": "Obyekt",
    "nav.home": "Ana səhifə", "nav.search": "Axtarış", "nav.add": "Elan ver",
    "nav.favorites": "Seçilmişlər", "nav.profile": "Profil", "nav.messages": "Mesajlar",
    "nav.compare": "Müqayisə", "nav.main": "Əsas naviqasiya", "nav.menu": "Menyu",
    "nav.dashboard": "İdarə paneli", "nav.moderation": "Moderasiya", "nav.logout": "Çıxış",
    "action.addListing": "Elan yerləşdir", "action.viewAll": "Hamısına bax", "action.search": "Axtar",
    "home.title.before": "Yeni məkanını", "home.title.highlight": "burada", "home.title.after": "tap.",
    "home.subtitle": "Azərbaycan üzrə mənzil, villa, torpaq, obyekt və digər daşınmaz əmlak elanlarını rahat şəkildə kəşf et.",
    "home.active": "aktiv elan", "home.popularArea": "populyar ərazi", "home.priceDropStat": "qiyməti endirilmiş elan",
    "home.new": "Yeni elanlar", "home.newSubtitle": "Son əlavə olunan elanlar",
    "home.premium": "Premium elanlar", "home.premiumSubtitle": "Seçilmiş yüksək keyfiyyətli daşınmaz əmlak",
    "home.priceDrops": "Qiyməti endirilənlər", "home.priceDropsSubtitle": "Satıcılar qiyməti endirib",
    "home.newBuildings": "Yeni tikililər", "home.newBuildingsSubtitle": "Müasir tikinti, təhvil verilən binalar",
    "home.popularAreas": "Populyar ərazilər", "home.popularAreasSubtitle": "Ən çox baxılan rayon və qəsəbələr",
    "listing.count": "elan", "listing.room": "otaq", "listing.floor": "mərtəbə",
    "listing.owner": "Mülkiyyətçi", "listing.agency": "Agentlik", "listing.new": "Yeni",
    "listing.priceDrop": "Qiymət düşüb", "listing.verified": "Təsdiqlənib", "listing.promoted": "Önə çıxarılıb",
    "listing.addFavorite": "Seçilmişlərə əlavə et", "listing.removeFavorite": "Seçilmişlərdən sil",
    "listing.addCompare": "Müqayisəyə əlavə et", "listing.removeCompare": "Müqayisədən sil",
    "listing.compareLimit": "Maksimum 4 elan müqayisə edilə bilər",
    "search.where": "Harada?", "search.allAreas": "Bütün ərazilər", "search.propertyType": "Əmlak növü",
    "search.allTypes": "Bütün növlər", "search.rooms": "Otaq", "search.any": "İstənilən",
    "search.price": "Qiymət", "search.popular": "Populyar ərazilər:", "search.upTo": "qədər", "search.from": "dən",
    "type.apartment": "Mənzil", "type.new_building": "Yeni tikili", "type.old_building": "Köhnə tikili", "type.house": "Həyət evi",
    "type.villa": "Villa", "type.land": "Torpaq", "type.commercial": "Obyekt", "type.office": "Ofis", "type.garage": "Qaraj",
    "footer.propertyTypes": "Əmlak növləri", "footer.apartments": "Mənzillər", "footer.houses": "Həyət evləri",
    "footer.villas": "Villalar", "footer.land": "Torpaq sahələri", "footer.commercial": "Kommersiya obyektləri",
    "footer.longRent": "Uzunmüddətli kirayə", "footer.dailyRent": "Günlük kirayə", "footer.apartmentRent": "Mənzil kirayə",
    "footer.officeRent": "Ofis kirayə", "footer.company": "Şirkət", "footer.about": "Haqqımızda",
    "footer.contact": "Əlaqə", "footer.info": "Məlumat", "footer.privacy": "Gizlilik siyasəti",
    "footer.terms": "İstifadəçi razılaşması", "footer.description": "Azərbaycan üzrə daşınmaz əmlak elanları üçün müasir platforma. Yeni məkanını burada tap.",
    "footer.rights": "Bütün hüquqlar qorunur.",
    "cookie.title": "Kukilərdən istifadə", "cookie.body": "Saytın işləməsi və təcrübənizi yaxşılaşdırmaq üçün kukilərdən istifadə edirik.",
    "cookie.accept": "Razıyam"
    ,"map.discover": "Xəritədə kəşf et", "map.viewAll": "Bütün elanları xəritədə gör"
    ,"auth.loginTitle": "Daxil olun", "auth.registerTitle": "Hesab yaradın", "auth.loginSubtitle": "Hesabınıza daxil olaraq davam edin.",
    "auth.registerSubtitle": "Elan yerləşdirmək və seçilmişləri saxlamaq üçün qeydiyyatdan keçin.", "auth.name": "Ad və soyad",
    "auth.phone": "Telefon", "auth.optional": "könüllü", "auth.email": "E-poçt", "auth.password": "Şifrə", "auth.forgot": "Şifrəni unutmusunuz?",
    "auth.wait": "Gözləyin…", "auth.login": "Daxil ol", "auth.register": "Qeydiyyatdan keç", "auth.haveAccount": "Artıq hesabınız var?",
    "auth.noAccount": "Hesabınız yoxdur?", "auth.loginLink": "Daxil olun", "auth.registerLink": "Qeydiyyatdan keçin", "auth.genericError": "Xəta baş verdi, yenidən cəhd edin",
    "auth.invalidEmail": "Düzgün e-poçt daxil edin", "auth.shortPassword": "Şifrə ən azı 8 simvol olmalıdır", "auth.nameRequired": "Ad daxil edin"
  },
  en: {
    "nav.sale": "Buy", "nav.rent": "Rent", "nav.daily": "Daily rent",
    "nav.newBuildings": "New buildings", "nav.house": "House", "nav.villa": "Villa", "nav.land": "Land", "nav.commercial": "Commercial",
    "nav.home": "Home", "nav.search": "Search", "nav.add": "Post listing", "nav.favorites": "Favorites", "nav.profile": "Profile",
    "nav.messages": "Messages", "nav.compare": "Compare", "nav.main": "Main navigation", "nav.menu": "Menu",
    "nav.dashboard": "Dashboard", "nav.moderation": "Moderation", "nav.logout": "Log out",
    "action.addListing": "Post a listing", "action.viewAll": "View all", "action.search": "Search",
    "home.title.before": "Find your new place", "home.title.highlight": "right here", "home.title.after": ".",
    "home.subtitle": "Discover apartments, villas, land, commercial spaces and other real estate listings across Azerbaijan.",
    "home.active": "active listings", "home.popularArea": "popular areas", "home.priceDropStat": "reduced-price listings",
    "home.new": "New listings", "home.newSubtitle": "Recently added properties", "home.premium": "Premium listings",
    "home.premiumSubtitle": "Selected high-quality properties", "home.priceDrops": "Price reductions", "home.priceDropsSubtitle": "Listings with recently reduced prices",
    "home.newBuildings": "New buildings", "home.newBuildingsSubtitle": "Modern newly delivered developments",
    "home.popularAreas": "Popular areas", "home.popularAreasSubtitle": "Most viewed districts and settlements",
    "listing.count": "listings", "listing.room": "rooms", "listing.floor": "floor", "listing.owner": "Owner", "listing.agency": "Agency",
    "listing.new": "New", "listing.priceDrop": "Price reduced", "listing.verified": "Verified", "listing.promoted": "Promoted",
    "listing.addFavorite": "Add to favorites", "listing.removeFavorite": "Remove from favorites", "listing.addCompare": "Add to comparison",
    "listing.removeCompare": "Remove from comparison", "listing.compareLimit": "You can compare up to 4 listings",
    "search.where": "Where?", "search.allAreas": "All areas", "search.propertyType": "Property type", "search.allTypes": "All types",
    "search.rooms": "Rooms", "search.any": "Any", "search.price": "Price", "search.popular": "Popular areas:", "search.upTo": "up to", "search.from": "from",
    "type.apartment": "Apartment", "type.new_building": "New building", "type.old_building": "Old building", "type.house": "House",
    "type.villa": "Villa", "type.land": "Land", "type.commercial": "Commercial", "type.office": "Office", "type.garage": "Garage",
    "footer.propertyTypes": "Property types", "footer.apartments": "Apartments", "footer.houses": "Houses", "footer.villas": "Villas",
    "footer.land": "Land", "footer.commercial": "Commercial properties", "footer.longRent": "Long-term rent", "footer.dailyRent": "Daily rent",
    "footer.apartmentRent": "Apartment rent", "footer.officeRent": "Office rent", "footer.company": "Company", "footer.about": "About us",
    "footer.contact": "Contact", "footer.info": "Information", "footer.privacy": "Privacy policy", "footer.terms": "Terms of use",
    "footer.description": "A modern platform for real estate listings across Azerbaijan. Find your new place here.", "footer.rights": "All rights reserved.",
    "cookie.title": "Cookie usage", "cookie.body": "We use cookies to operate the site and improve your experience.", "cookie.accept": "Accept"
    ,"map.discover": "Explore on the map", "map.viewAll": "View all listings on the map"
    ,"auth.loginTitle": "Sign in", "auth.registerTitle": "Create an account", "auth.loginSubtitle": "Sign in to continue to your account.",
    "auth.registerSubtitle": "Register to post listings and save favorites.", "auth.name": "Full name", "auth.phone": "Phone",
    "auth.optional": "optional", "auth.email": "Email", "auth.password": "Password", "auth.forgot": "Forgot your password?",
    "auth.wait": "Please wait…", "auth.login": "Sign in", "auth.register": "Register", "auth.haveAccount": "Already have an account?",
    "auth.noAccount": "Don't have an account?", "auth.loginLink": "Sign in", "auth.registerLink": "Register", "auth.genericError": "Something went wrong. Please try again",
    "auth.invalidEmail": "Enter a valid email", "auth.shortPassword": "Password must be at least 8 characters", "auth.nameRequired": "Enter your name"
  },
  ru: {
    "nav.sale": "Купить", "nav.rent": "Аренда", "nav.daily": "Посуточно", "nav.newBuildings": "Новостройки",
    "nav.house": "Дом", "nav.villa": "Вилла", "nav.land": "Земля", "nav.commercial": "Коммерция",
    "nav.home": "Главная", "nav.search": "Поиск", "nav.add": "Подать объявление", "nav.favorites": "Избранное", "nav.profile": "Профиль",
    "nav.messages": "Сообщения", "nav.compare": "Сравнение", "nav.main": "Основная навигация", "nav.menu": "Меню",
    "nav.dashboard": "Панель управления", "nav.moderation": "Модерация", "nav.logout": "Выйти",
    "action.addListing": "Разместить объявление", "action.viewAll": "Смотреть все", "action.search": "Найти",
    "home.title.before": "Найдите новое жильё", "home.title.highlight": "здесь", "home.title.after": ".",
    "home.subtitle": "Удобный поиск квартир, вилл, земельных участков, коммерческих объектов и другой недвижимости по Азербайджану.",
    "home.active": "активных объявлений", "home.popularArea": "популярных районов", "home.priceDropStat": "объявлений со сниженной ценой",
    "home.new": "Новые объявления", "home.newSubtitle": "Недавно добавленная недвижимость", "home.premium": "Премиум объявления",
    "home.premiumSubtitle": "Отобранная качественная недвижимость", "home.priceDrops": "Цены снижены", "home.priceDropsSubtitle": "Объявления с недавно сниженной ценой",
    "home.newBuildings": "Новостройки", "home.newBuildingsSubtitle": "Современные сданные жилые комплексы",
    "home.popularAreas": "Популярные районы", "home.popularAreasSubtitle": "Самые просматриваемые районы и посёлки",
    "listing.count": "объявлений", "listing.room": "комнат", "listing.floor": "этаж", "listing.owner": "Собственник", "listing.agency": "Агентство",
    "listing.new": "Новое", "listing.priceDrop": "Цена снижена", "listing.verified": "Проверено", "listing.promoted": "Продвигается",
    "listing.addFavorite": "Добавить в избранное", "listing.removeFavorite": "Удалить из избранного", "listing.addCompare": "Добавить к сравнению",
    "listing.removeCompare": "Удалить из сравнения", "listing.compareLimit": "Можно сравнить не более 4 объявлений",
    "search.where": "Где?", "search.allAreas": "Все районы", "search.propertyType": "Тип недвижимости", "search.allTypes": "Все типы",
    "search.rooms": "Комнаты", "search.any": "Любое", "search.price": "Цена", "search.popular": "Популярные районы:", "search.upTo": "до", "search.from": "от",
    "type.apartment": "Квартира", "type.new_building": "Новостройка", "type.old_building": "Старый фонд", "type.house": "Дом",
    "type.villa": "Вилла", "type.land": "Земля", "type.commercial": "Коммерческий объект", "type.office": "Офис", "type.garage": "Гараж",
    "footer.propertyTypes": "Типы недвижимости", "footer.apartments": "Квартиры", "footer.houses": "Дома", "footer.villas": "Виллы",
    "footer.land": "Земельные участки", "footer.commercial": "Коммерческие объекты", "footer.longRent": "Долгосрочная аренда",
    "footer.dailyRent": "Посуточная аренда", "footer.apartmentRent": "Аренда квартир", "footer.officeRent": "Аренда офисов",
    "footer.company": "Компания", "footer.about": "О нас", "footer.contact": "Контакты", "footer.info": "Информация",
    "footer.privacy": "Политика конфиденциальности", "footer.terms": "Условия использования",
    "footer.description": "Современная платформа объявлений о недвижимости по всему Азербайджану. Найдите новое жильё здесь.", "footer.rights": "Все права защищены.",
    "cookie.title": "Использование файлов cookie", "cookie.body": "Мы используем cookie для работы сайта и улучшения вашего опыта.", "cookie.accept": "Принять"
    ,"map.discover": "Искать на карте", "map.viewAll": "Все объявления на карте"
    ,"auth.loginTitle": "Войти", "auth.registerTitle": "Создать аккаунт", "auth.loginSubtitle": "Войдите, чтобы продолжить.",
    "auth.registerSubtitle": "Зарегистрируйтесь, чтобы размещать объявления и сохранять избранное.", "auth.name": "Имя и фамилия",
    "auth.phone": "Телефон", "auth.optional": "необязательно", "auth.email": "Эл. почта", "auth.password": "Пароль", "auth.forgot": "Забыли пароль?",
    "auth.wait": "Подождите…", "auth.login": "Войти", "auth.register": "Зарегистрироваться", "auth.haveAccount": "Уже есть аккаунт?",
    "auth.noAccount": "Нет аккаунта?", "auth.loginLink": "Войти", "auth.registerLink": "Зарегистрироваться", "auth.genericError": "Произошла ошибка. Попробуйте снова",
    "auth.invalidEmail": "Введите корректный адрес эл. почты", "auth.shortPassword": "Пароль должен содержать не менее 8 символов", "auth.nameRequired": "Введите имя"
  }
} as const;

export type MessageKey = keyof typeof messages.az;

export function translate(locale: Locale, key: MessageKey): string {
  return messages[locale][key] ?? messages.az[key];
}

export function roomLabel(locale: Locale, count: number): string {
  if (locale === "az") return "otaq";
  if (locale === "en") return count === 1 ? "room" : "rooms";
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return "комната";
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return "комнаты";
  return "комнат";
}
