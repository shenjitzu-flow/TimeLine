import streamlit as st
import random
import io
from PIL import Image, ImageDraw, ImageFont

# --- FUNCIONES DE DIBUJO (Las mismas, adaptadas para web) ---
def crear_polaroid(imagen_subida, texto_anio):
    try:
        # Streamlit entrega el archivo en memoria, Pillow lo lee directo
        img = Image.open(imagen_subida).convert('RGBA')
        min_dim = min(img.size)
        img_cuadrada = img.crop(( (img.width - min_dim)/2, (img.height - min_dim)/2, 
                                  (img.width + min_dim)/2, (img.height + min_dim)/2 ))
        img_cuadrada = img_cuadrada.resize((800, 800), Image.LANCZOS)
        
        polaroid = Image.new('RGBA', (900, 1100), 'white')
        polaroid.paste(img_cuadrada, (50, 50))
        draw = ImageDraw.Draw(polaroid)
        draw.rectangle([(0, 0), (899, 1099)], outline="#CCCCCC", width=4) 
        
        try: fuente = ImageFont.truetype("arial.ttf", 60)
        except: fuente = ImageFont.load_default()
            
        bbox = draw.textbbox((0, 0), texto_anio, font=fuente)
        pos_x = (900 - (bbox[2] - bbox[0])) / 2
        draw.text((pos_x, 930), texto_anio, fill="#222222", font=fuente)
        
        angulo = random.uniform(-4.5, 4.5)
        polaroid_rotada = polaroid.rotate(angulo, resample=Image.BICUBIC, expand=True)
        return polaroid_rotada
    except Exception as e:
        st.error(f"Error procesando una imagen: {e}")
        return None

def dibujar_marco_leds(hoja):
    draw = ImageDraw.Draw(hoja)
    margen = 80
    draw.rectangle([(margen, margen), (hoja.width-margen, hoja.height-margen)], outline="#222222", width=6)
    puntos = []
    for x in range(margen, hoja.width-margen, 250): puntos.append((x, margen)); puntos.append((x, hoja.height-margen))
    for y in range(margen + 250, hoja.height-margen, 250): puntos.append((margen, y)); puntos.append((hoja.width-margen, y))
    colores = [(255, 60, 60), (60, 255, 60), (60, 150, 255), (255, 230, 60), (255, 80, 255)]
    capa_luces = Image.new('RGBA', hoja.size, (0,0,0,0))
    draw_luces = ImageDraw.Draw(capa_luces)
    for px, py in puntos:
        lx, ly = px + random.randint(-15, 15), py + random.randint(-15, 15)
        color = random.choice(colores)
        draw_luces.ellipse((lx-50, ly-50, lx+50, ly+50), fill=color + (60,))
        draw_luces.ellipse((lx-14, ly-14, lx+14, ly+14), fill=color + (255,))
        draw_luces.rectangle([(lx-8, ly-22), (lx+8, ly-14)], fill="#111")
    return Image.alpha_composite(hoja, capa_luces)

def get_y_mecate(x, base_y):
    return (-180 / ((3300 / 2) ** 2)) * ((x - 3300 / 2) ** 2) + base_y + 180

def dibujar_mecate(hoja, base_y):
    draw = ImageDraw.Draw(hoja)
    puntos = [(x, get_y_mecate(x, base_y)) for x in range(0, hoja.width + 1, 20)]
    draw.line(puntos, fill="#C29A69", width=16, joint="curve")

# --- LA INTERFAZ WEB (STREAMLIT) ---

st.set_page_config(page_title="Línea de Tiempo", layout="centered")

st.title("📸 Creador de Línea de Tiempo Escolar")
st.write("Sube las fotos de cada año y genera un PDF con diseño rústico de foquitos, listo para imprimir en hojas negras.")

# 1. Pedir los años
anios_input = st.text_input("1. Escribe los años que quieres incluir separados por coma (Ej. 2017, 2018, 2019):")

if anios_input:
    anios_lista = [a.strip() for a in anios_input.split(',')]
    fotos_seleccionadas = {}
    
    st.write("---")
    st.write("### 2. Sube tus fotos por año")
    st.write("Sube máximo 3 fotos por cada bloque. Se acomodarán de izquierda a derecha.")
    
    # 2. Crear una sección de subida por cada año
    for anio in anios_lista:
        if anio:
            with st.expander(f"📥 Fotos del año {anio}", expanded=True):
                archivos = st.file_uploader(f"Selecciona las fotos (Max 3)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=anio)
                if archivos:
                    if len(archivos) > 3:
                        st.warning("¡Ojo! Subiste más de 3 fotos. Solo se usarán las primeras 3.")
                        fotos_seleccionadas[anio] = archivos[:3]
                    else:
                        fotos_seleccionadas[anio] = archivos
                        
    # 3. Botón Mágico
    if len(fotos_seleccionadas) > 0:
        st.write("---")
        if st.button("✨ Generar PDF de Línea de Tiempo", type="primary"):
            with st.spinner('Ensamblando la magia... esto puede tardar unos segundos.'):
                
                anios_ord = sorted(fotos_seleccionadas.keys())
                num_h = (len(anios_ord) + 1) // 2
                hojas_pdf = [Image.new('RGBA', (3300, 2550), (12, 12, 12, 255)) for _ in range(num_h)]

                for i in range(num_h):
                    hojas_pdf[i] = dibujar_marco_leds(hojas_pdf[i])
                    dibujar_mecate(hojas_pdf[i], 250)
                    dibujar_mecate(hojas_pdf[i], 1450)

                for k, anio_linea in enumerate(anios_ord):
                    page_idx = k // 2 
                    base_y = 250 if k % 2 == 0 else 1450 
                    fotos = fotos_seleccionadas[anio_linea]
                    
                    posiciones_base = [600, 1650, 2700]
                    cx = posiciones_base[:len(fotos)]
                    hoja = hojas_pdf[page_idx]
                    draw_p = ImageDraw.Draw(hoja)
                    
                    for idx, archivo_subido in enumerate(fotos):
                        # Aquí le mandamos el archivo directo de la web y el texto del año
                        pol = crear_polaroid(archivo_subido, anio_linea) 
                        
                        if pol:
                            xc = cx[idx]
                            ym = get_y_mecate(xc, base_y)
                            hoja.paste(pol, (xc - pol.width//2, int(ym)-20), mask=pol)
                            draw_p.rectangle([(xc-18, int(ym)-45), (xc+18, int(ym)+25)], fill="#8B5A2B")
                            draw_p.rectangle([(xc-20, int(ym)-5), (xc+20, int(ym)+5)], fill="#B0C4DE")

                hojas_rgb = [h.convert('RGB') for h in hojas_pdf]
                
                if hojas_rgb:
                    # Guardar el PDF en la memoria RAM (no en el disco) para descargarlo
                    pdf_buffer = io.BytesIO()
                    hojas_rgb[0].save(pdf_buffer, format='PDF', save_all=True, append_images=hojas_rgb[1:], resolution=300.0)
                    
                    st.success("¡PDF Generado con éxito!")
                    
                    # Botón de descarga web
                    st.download_button(
                        label="⬇️ Descargar PDF Listo para Imprimir",
                        data=pdf_buffer.getvalue(),
                        file_name="Linea_del_Tiempo.pdf",
                        mime="application/pdf"
                    )