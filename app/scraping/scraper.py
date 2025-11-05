import cv2
import pytesseract
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os


load_dotenv()

uf_to_state_name = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins"
}


def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # Definir um tamanho ajuda com elementos
    options.add_argument("window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    return driver


def parse_ocr_situacao(ocr_text: str) -> str:
    """
    Processa o texto bruto do OCR e o transforma em um dicionário estruturado.
    """
    lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
    print(lines)
    situacao = lines[-1]
    print("situacao = ",situacao)
    situacao_aux = []
    situacao_aux = situacao.split()
    indice_situacao = situacao_aux.index("SITUAÇÃO")
    tipo_situacao = situacao_aux[indice_situacao+1]
    
    return tipo_situacao


def process_image_with_ocr(image_bytes: bytes) -> str:
    """Carrega os bytes da imagem, processa com CV2 e extrai texto com Tesseract."""
    try:
        
        nparr = np.frombuffer(image_bytes, np.uint8)

        
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        
        _, thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        

        
        config = '--psm 6'  
        text = pytesseract.image_to_string(thresh, lang='por', config=config)

        print(text)

        return text

    

    except Exception as e:
        print(f"Erro durante o processamento de OCR: {e}")
        return ""


def fetch_lawyer_data(name: str, uf: str) -> dict:
    driver = get_driver()
    url = os.getenv("SITE_OAB")
    if not url:
        return {"error": "Variável de ambiente SITE_OAB não definida."}

    driver.get(url)

    scraped_data = {}  

    try:
        wait = WebDriverWait(driver, 20)

        name_field = wait.until(
            EC.presence_of_element_located((By.ID, "txtName")))
        name_field.send_keys(name)

        uf_upper = uf.upper()
        if uf_upper not in uf_to_state_name:
            return {"error": f"UF '{uf}' é inválida."}

        state_name = uf_to_state_name[uf_upper]
        option_text = f"Conselho Seccional - {state_name}"

        uf_select_element = wait.until(
            EC.presence_of_element_located((By.ID, "cmbSeccional")))
        uf_select = Select(uf_select_element)
        uf_select.select_by_visible_text(option_text)

        search_button = driver.find_element(By.ID, "btnFind")
        search_button.click()

       
        try:
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#divResult .row")))
        except TimeoutException:
            not_found_element = driver.find_element(By.ID, "textResult")
            if "não retornou nenhum resultado" in not_found_element.text:
                return {"error": "Advogado não encontrado."}
            else:
                raise TimeoutException(
                    "A página não carregou resultados nem a mensagem de erro esperada.")

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        first_result = soup.find("div", class_="row")

        nome_div = first_result.find(class_="rowName")
        nome = nome_div.find_all(
            'span')[-1].text.strip() if nome_div else "Não informado"

        tipo_div = first_result.find(class_="rowTipoInsc")
        categoria = tipo_div.find_all(
            'span')[-1].text.strip() if tipo_div else "Não informado"

        insc_div = first_result.find(class_="rowInsc")
        oab = insc_div.find_all(
            'span')[-1].text.strip() if insc_div else "Não informado"

        uf_div = first_result.find(class_="rowUf")
        uf_seccional = uf_div.find_all(
            'span')[-1].text.strip() if uf_div else "Não informado"

        print("fim da primeira parte")

        #inicio do uso da visão

        first_result_aux = driver.find_element(By.CLASS_NAME, "row")
        first_result_aux.click()

        image_locator = (By.ID, "imgDetail")
        img_element = wait.until(
            EC.visibility_of_element_located(image_locator))

        image_bytes = img_element.screenshot_as_png

        ocr_text = process_image_with_ocr(image_bytes)

        print("chamou o processamento de imagem")

        scraped_data["ocr_raw_text"] = ocr_text

        ocr_data = parse_ocr_situacao(ocr_text)

        print("deu o parse")
        print(ocr_data)

        dict = {
            "oab": oab,
            "nome": nome,
            "uf": uf_seccional,
            "categoria": categoria,
            "data_inscricao": "Não listado",
            "situacao": ocr_data
        }

        return dict

    except TimeoutException:
        return {"error": "A página demorou muito para responder ou um elemento não foi encontrado (Timeout)."}
    except Exception as e:
        return {"error": f"Ocorreu um erro inesperado: {str(e)}"}
    finally:
        driver.quit()
