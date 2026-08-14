import { cookies } from "next/headers";
import { LOCALE_COOKIE, normalizeLocale, translate } from "./i18n";

export async function getLocale() {
  return normalizeLocale((await cookies()).get(LOCALE_COOKIE)?.value);
}

export async function getTranslations() {
  const locale = await getLocale();
  return { locale, t: (key: Parameters<typeof translate>[1]) => translate(locale, key) };
}
