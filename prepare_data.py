import pandas as pd
import os

# Baca data CSV
df = pd.read_csv('dummy/data_stunting_dummy.csv')

# Hitung prevalensi stunting
df['prevalensi_stunting'] = round(
    (df['jumlah_stunting'] / df['jumlah_balita']) * 100, 2
)

# Klasifikasi kategori stunting
def klasifikasi(val):
    if val < 10:   return 'Rendah'
    elif val < 20: return 'Sedang'
    elif val < 30: return 'Tinggi'
    else:          return 'Sangat Tinggi'

df['kategori_stunting'] = df['prevalensi_stunting'].apply(klasifikasi)

# Hitung skor kerentanan sederhana (semakin tinggi = lebih rentan)
# Bobot: stunting 40%, kemiskinan 30%, sanitasi 30%
df['skor_kerentanan'] = (
    (df['prevalensi_stunting'] / 100) * 0.4 +
    (df['penerima_bansos'] / df['jumlah_balita']) * 0.3 +
    ((100 - df['sanitasi_layak']) / 100) * 0.3
)

def kategori_rentan(val):
    if val < 0.2:   return 'Aman'
    elif val < 0.35: return 'Waspada'
    elif val < 0.5:  return 'Rentan'
    else:            return 'Sangat Rentan'

df['kategori_kerentanan'] = df['skor_kerentanan'].apply(kategori_rentan)

# Simpan hasil
os.makedirs('processed', exist_ok=True)
df.to_csv('processed/data_stunting_final.csv', index=False)
print("Selesai! File tersimpan di data/processed/data_stunting_final.csv")
print(df[['nama_wilayah','prevalensi_stunting','kategori_stunting','kategori_kerentanan']])