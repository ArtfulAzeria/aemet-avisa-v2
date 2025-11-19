import Constant as CONS
from Utils import Utils
import Color

import os
import io
import re
import cv2
import requests
import numpy as np
from PIL import Image
import geopandas as gpd
import contextily as ctx
from atproto import Client, client_utils
from datetime import datetime, timedelta
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import matplotlib.patches as mpatches

if not os.path.exists(CONS.AEMET_GEOJSON):
    raise FileNotFoundError(f"El archivo {CONS.AEMET_GEOJSON} no existe")

class Main:
    def __init__(self, mock: False):
        self.mock = mock
        if self.mock:
            self.rssponse = CONS.MOCK_RSS
        else:
            self.rssponse = requests.get(CONS.AEMET_RSS)
        self.geojsonAemet = gpd.read_file(CONS.AEMET_GEOJSON).to_crs(epsg=3857)
        self.geojsonCommunities = gpd.read_file(CONS.COMMUNITIES_GEOJSON).to_crs(epsg=3857)
        self.fig_base, self.ax_base = plt.subplots(figsize=(10, 10))
        self.fig_final, self.ax_final = plt.subplots()
        self.aemet_warning_set = {}
        self.comm_set = {}
        self.y_quanto = 0
        self.o_quanto = 0
        self.r_quanto = 0
        self.full_map = None
        self.canary_islands = None
        self.final_map = None

    def map_highlight(self):
        land = self.geojsonAemet[~self.geojsonAemet['COD_Z'].str.endswith('C', na=False)]
        coast = self.geojsonAemet[self.geojsonAemet['COD_Z'].str.endswith('C', na=False)]
        communities = self.geojsonCommunities

        land.plot(ax=self.ax_base, color=Color.SMOKE_WHITE)
        coast.plot(ax=self.ax_base, color=Color.POWDER_WHITE, edgecolor=Color.ASH_GREY)
        communities.plot(ax=self.ax_base, color=Color.MISCHIEF_ALPHA, edgecolor=Color.ASH_GREY)

    def extract_dates(self, consumed_string):
        return re.findall(r"(\d{2}:\d{2} \d{2}-\d{2}-\d{4})", consumed_string)

    def save_data(self, aemet_warning_lvl, code, date_tuple, mock):
        current_date = datetime.now()

        date_format = "%H:%M %d-%m-%Y"
        ini_date = datetime.strptime(date_tuple[0], date_format)
        end_date = datetime.strptime(date_tuple[1], date_format)

        if mock :
            ini_date = current_date-timedelta(hours=1)
            end_date = current_date+timedelta(hours=1)

        if ini_date < current_date < end_date:
            if aemet_warning_lvl == "amarillo":
                self.y_quanto += 1
            elif aemet_warning_lvl == "naranja":
                self.o_quanto += 1
            elif aemet_warning_lvl == "rojo":
                self.r_quanto += 1

            if code not in self.aemet_warning_set:
                self.aemet_warning_set[code] = aemet_warning_lvl
            elif self.aemet_warning_set[code] == "amarillo" and (aemet_warning_lvl == "naranja" or aemet_warning_lvl == "rojo"):
                self.aemet_warning_set[code] = aemet_warning_lvl
            elif self.aemet_warning_set[code] == "naranja" and aemet_warning_lvl == "rojo":
                self.aemet_warning_set[code] = aemet_warning_lvl

    def draw_polygon(self):
        for code in self.aemet_warning_set:
            self.comm_check(self.aemet_warning_set[code], code)
            if self.aemet_warning_set[code] == "amarillo":
                aemet_warning = self.geojsonAemet[self.geojsonAemet["COD_Z"] == code]
                aemet_warning.plot(ax=self.ax_base, color=Color.DARK_YELLOW, edgecolor=Color.LIGHT_YELLOW)
            elif self.aemet_warning_set[code] == "naranja":
                aemet_warning = self.geojsonAemet[self.geojsonAemet["COD_Z"] == code]
                aemet_warning.plot(ax=self.ax_base, color=Color.DARK_ORANGE, edgecolor=Color.LIGHT_ORANGE)
            elif self.aemet_warning_set[code] == "rojo":
                aemet_warning = self.geojsonAemet[self.geojsonAemet["COD_Z"] == code]
                aemet_warning.plot(ax=self.ax_base, color=Color.DARK_RED, edgecolor=Color.LIGHT_RED)

    def comm_check(self, aemet_warning_lvl, cod_z):
        comm = self.geojsonAemet[self.geojsonAemet["COD_Z"] == cod_z].iloc[0]["NOM_CCAA"]

        if comm in CONS.COMM_PARSE:
            comm = CONS.COMM_PARSE[comm]

        if comm not in self.comm_set:
            self.comm_set[comm] = aemet_warning_lvl
        elif self.comm_set[comm] == "amarillo" and (aemet_warning_lvl == "naranja" or aemet_warning_lvl == "rojo"):
            self.comm_set[comm] = aemet_warning_lvl
        elif self.comm_set[comm] == "naranja" and aemet_warning_lvl == "rojo":
            self.comm_set[comm] = aemet_warning_lvl

    def post_text(self):
        if self.mock:
            return "Esto es una prueba. Ninguno de los datos mostrados son reales."

        text = ""

        aemet_warning_groups = {}
        for comm, color in self.comm_set.items():
            aemet_warning_groups.setdefault(color, []).append(comm)

        color_parse = {
            'rojo': '🔴 Aviso rojo',
            'naranja': '🟠 Aviso naranja',
            'amarillo': '🟡 Aviso amarillo'
        }

        for color in ["rojo", "naranja", "amarillo"]:
            if color in aemet_warning_groups:
                comm = aemet_warning_groups[color]
                if len(comm) > 1:
                    comm[-1] = "y " + comm[-1]  # Añadir 'y' al último elemento
                    text += f"{color_parse[color]} en:\n{', '.join(comm)}\n"
                else:
                    text += f"{color_parse[color]} en:\n{comm[0]}\n"

        if text == "":
            text = "🟢 Actualmente no hay ningún aviso activo.\n"

        text += f"\nPara más información acude a "

        return text

    def save_image(self):
        plt.savefig("../resources/media/full_map.png", dpi=300, bbox_inches='tight', pad_inches=0)

    def clean_image(self):
        Utils.clean_img(self.ax_base, self.fig_base)
        Utils.clean_img(self.ax_final, self.fig_final)

    def load_map(self):
        ctx.add_basemap(self.ax_base, source=ctx.providers.Esri.WorldTerrain)

        for img in self.ax_base.images:
            img_data = np.array(img.get_array())
            img_gray = np.dot(img_data[..., :3], [0.2989, 0.5870, 0.1140])
            img_gray = np.clip(img_gray * 0.3, 0, 255)
            img_gray = img_gray.astype(np.uint8)
            img_gray = np.stack([img_gray] * 3, axis=-1)
            img.set_array(img_gray)

    def extract_data(self):
        if self.mock:
            root = ET.parse(self.rssponse).getroot()
        else:
            root = ET.fromstring(self.rssponse.content)

        channel = root.find('channel')

        for item in channel.findall('item'):
            title = item.find('title').text
            link = item.find('link').text
            description = item.find('description').text

            code = re.search(r"_AFAZ(\w{7})", link).group(1)
            if code[-1] != "C":
                code = code[:-1]

            aemet_warning = title.split("Nivel ")[1].split()[0].rstrip(".")
            date_tuple = self.extract_dates(description)
            self.save_data(aemet_warning, code, date_tuple, self.mock)

    def plt_to_image(self):
        buf = io.BytesIO()
        self.fig_base.savefig(buf, format="png", dpi=300, bbox_inches='tight', pad_inches=0)
        buf.seek(0)

        file_bytes = np.asarray(bytearray(buf.read()), dtype=np.uint8)
        self.full_map = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    def gen_final_map(self):
        full_map = self.full_map
        self.canary_islands = full_map[1720:2000, 90:620]
        ci_y, ci_x = self.canary_islands.shape[:2]
        pip_x = 620
        pip_y = 1000

        full_map[pip_y:pip_y + ci_y, pip_x:pip_x + ci_x] = self.canary_islands
        self.final_map = full_map

        cv2.rectangle(self.final_map, (pip_x, pip_y), (pip_x + ci_x, pip_y + ci_y), Utils.rgba_to_bgr(Color.ASH_GREY), 3)
        self.final_map = self.final_map[70:1300, 600:2240]
        self.ax_final.imshow(cv2.cvtColor(self.final_map, cv2.COLOR_BGR2RGB), aspect='auto')

    def final_data(self):
        legend_patches = [
            mpatches.Patch(color=Color.DARK_YELLOW, label=f"Amarillo ({self.y_quanto})"),
            mpatches.Patch(color=Color.DARK_ORANGE, label=f"Naranja ({self.o_quanto})"),
            mpatches.Patch(color=Color.DARK_RED, label=f"Rojo ({self.r_quanto})"),
        ]
        self.ax_final.legend(handles=legend_patches, title="⚠ Avisos activos", loc="lower right", framealpha=0.4)

        map_datetime = datetime.now().strftime("%d-%m-%Y\n%H:%M:%S")

        self.ax_final.text(0.99, 0.92, map_datetime, transform=self.ax_final.transAxes,
                fontsize=8, color=Color.SMOKE_WHITE, ha="right", va="bottom", fontweight="bold")

        plt.savefig("../resources/media/final_map.png", dpi=300, bbox_inches='tight', pad_inches=0)

    # def aemet_warnings_by_commm(self):

is_mock = False

load_dotenv()
client = Client()
client.login(os.getenv("BLUESKY_USERNAME"), os.getenv("BLUESKY_PASSWORD"))

main = Main(is_mock)
main.map_highlight()
main.extract_data()
main.draw_polygon()
main.clean_image()
main.load_map()
main.save_image()
main.plt_to_image()
main.gen_final_map()
main.final_data()
text = main.post_text()

image = cv2.imread("../resources/media/final_map.png")

image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
image_pil = Image.fromarray(image)

buffer = io.BytesIO()
image_pil.save(buffer, format="PNG")

post = client.send_image(
    client_utils.TextBuilder().text(text).link("www.aemet.es", "https://www.aemet.es/es/eltiempo/prediccion/avisos"),
    buffer.getvalue(),
    "Mapa AEMET"
)