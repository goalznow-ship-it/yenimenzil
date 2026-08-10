export interface DemoImage {
  src: string;
  alt: string;
}

const unsplash = (id: string, alt: string): DemoImage => ({
  src: `https://images.unsplash.com/${id}?auto=format&fit=crop&w=1400&q=80`,
  alt
});

export const IMAGE_POOL: Record<string, DemoImage> = {
  livingModern: unsplash("photo-1522708323590-d24dbb6b0267", "Müasir qonaq otağı"),
  livingLight: unsplash("photo-1560448204-e02f11c3d0e2", "İşıqlı qonaq otağı"),
  livingScandi: unsplash("photo-1502672260266-1c1ef2d93688", "Skandinav üslublu qonaq otağı"),
  livingComfort: unsplash("photo-1554995207-c18c203602cb", "Rahat qonaq otağı"),
  livingElegant: unsplash("photo-1567767292278-a4f21aa2d36e", "Eleqant qonaq otağı"),
  livingBeige: unsplash("photo-1493809842364-78817add7ffb", "Bej tonlarda qonaq otağı"),
  bedroomCozy: unsplash("photo-1505691938895-1758d7feb511", "Yataq otağı"),
  bedroomModern: unsplash("photo-1522771739844-6a9f6d5f14af", "Müasir yataq otağı"),
  bedroomWarm: unsplash("photo-1583847268964-b28dc8f51f92", "Yataq otağı"),
  bedroomSerene: unsplash("photo-1560185007-cde436f6a4d0", "Sakit yataq otağı"),
  kitchenWhite: unsplash("photo-1556912173-3bb406ef7e77", "Ağ mətbəx"),
  kitchenWood: unsplash("photo-1556909212-d5b604d0c90d", "Ağac üzlüklü mətbəx"),
  kitchenModern: unsplash("photo-1600489000022-c2086d79f9d4", "Müasir mətbəx"),
  kitchenIsland: unsplash("photo-1571508601891-ca5e7a713859", "Ada mətbəx"),
  interiorLux: unsplash("photo-1600210492486-724fe5c67fb0", "Lüks interyer"),
  interiorGreen: unsplash("photo-1600121848594-d8644e57abab", "Dizayn interyer"),
  houseModern: unsplash("photo-1600585154340-be6161a56a0c", "Müasir ev fasadı"),
  houseWhite: unsplash("photo-1600596542815-ffad4c1539a9", "Ağ ev fasadı"),
  houseLux: unsplash("photo-1600607687939-ce8a6c25118c", "Lüks ev fasadı"),
  houseGreen: unsplash("photo-1600566753086-00f18fb6b3ea", "Yaşıllıqlı ev"),
  houseClassic: unsplash("photo-1512917774080-9991f1c4c750", "Klassik ev fasadı"),
  houseSide: unsplash("photo-1568605114967-8130f3a36994", "Ev fasadı"),
  housePool: unsplash("photo-1580587771525-78b9dba3b914", "Hovuzlu ev"),
  houseDrive: unsplash("photo-1600047509807-ba8f99d2cdde", "Avtomobil yolu ilə ev"),
  houseTerraced: unsplash("photo-1570129477492-45c003edd2be", "Teraslı ev"),
  villaPool: unsplash("photo-1613490493576-7fde63acd811", "Hovuzlu villa"),
  villaModern: unsplash("photo-1613977257363-707ba9348227", "Müasir villa"),
  villaClassic: unsplash("photo-1416331108676-a22ccb276e35", "Klassik villa"),
  houseBackyard: unsplash("photo-1518780664697-55e3ad937233", "Həyət evi"),
  apartmentBuilding: unsplash("photo-1545324418-cc1a3fa10c00", "Yaşayış binası"),
  apartmentBlock: unsplash("photo-1460317442991-0ec209397118", "Çoxmərtəbəli bina"),
  apartmentComplex: unsplash("photo-1479839672679-a46483c0e7c8", "Yeni tikili kompleksi"),
  officeOpen: unsplash("photo-1524758631624-e2822e304c36", "Ofis interyeri"),
  officeMeeting: unsplash("photo-1497366754035-f200968a6e72", "Ofis görüş otağı"),
  officeLobby: unsplash("photo-1497366811353-6870744d04b2", "Ofis lobbisi"),
  landField: unsplash("photo-1500382017468-9049fed747ef", "Torpaq sahəsi"),
  landGreen: unsplash("photo-1470770841072-f978cf4d019e", "Yaşıl torpaq sahəsi"),
  landPlot: unsplash("photo-1523895665936-7bfe172b757d", "Torpaq sahəsi"),
  retailShop: unsplash("photo-1441986300917-64674bd600d8", "Ticarət obyekti"),
  cityBaku: unsplash("photo-1449824913935-59a10b8d2000", "Şəhər mənzərəsi")
};

export function demoImages(keys: string[]): DemoImage[] {
  const selected: DemoImage[] = [];
  for (const key of keys) {
    const image = IMAGE_POOL[key];
    if (image) selected.push(image);
  }
  return selected;
}
