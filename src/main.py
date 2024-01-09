import asyncio
import base64
import re
import uuid

import aiofiles
import httpx
import pyuseragents

from datetime import datetime
from bs4 import BeautifulSoup
from loguru import logger
from database import OffendersData

from .captcha import Captcha


sem = asyncio.Semaphore(1)


class LowaOffendersScraper(httpx.AsyncClient):
    def __init__(self, config: dict):
        super().__init__()
        self.search_url: str = "https://www.iowasexoffender.gov/simplesearch/"
        self.config = config
        self.total_pages = None

        self.offenders_urls = []
        self.headers = {
            'authority': 'www.iowasexoffender.gov',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
            'cache-control': 'max-age=0',
            'user-agent': pyuseragents.random(),
        }

        self.timeout = 5
        self.max_attempts = 3


    async def solve_captcha(self, image_data: str) -> str:
        """Solve captcha using 2Captcha service"""

        async with aiofiles.open(f"./temp/{image_data}", 'rb') as f:
            result = await Captcha(
                image_data=str(base64.b64encode(await f.read()), "utf-8"),
                api_key=self.config["two_captcha_api_key"],
            ).solve()

        return result


    async def download_image(self, url: str) -> str:
        """Download captcha image from url and save it to ./temp/ folder"""
        image_name = f"{uuid.uuid4().hex}.jpg"

        async with self.stream('GET', url) as response:
            async with aiofiles.open(f"./temp/{image_name}", 'wb') as f:
                async for chunk in response.aiter_bytes():
                    await f.write(chunk)

        return image_name


    @staticmethod
    def get_captcha_url(html: str) -> str:
        captcha_url = re.search(r'<img id="siimage" alt="captcha text" src="(https?://\S+)" />', html)
        if not captcha_url:
            raise Exception("Captcha url not found while validating session")

        captcha_url = captcha_url.group(1)
        logger.info(f"Captcha url: {captcha_url}")
        return captcha_url


    async def validate_session(self) -> None:
        attempts = 0

        while attempts < self.max_attempts:
            params = {
                'type': 'simple',
                'lastname': '',
                'firstname': '',
                'alias': '1',
                'postalcode': '',
                'action': 'Submit Search',
            }
            response = await self.get(self.search_url, params=params)

            captcha_url = self.get_captcha_url(response.text)
            image = await self.download_image(captcha_url)
            captcha_code = await self.solve_captcha(image)

            data = {
                'agreement': '=== PUBLIC NOTICE AND DISCLAIMER ===\r\n\r\n1) This site does not contain the entire list of sex offenders registered in Iowa.\r\n\r\n2) Your community law enforcement and county sheriff\'s office are aware that these subjects are in the community.\r\n\r\n3) Any actions taken by you against these subjects, including vandalism of property, verbal or written threats of harm or physical assault against these subjects, their families or employers can result in your arrest and prosecution.\r\n\r\n4) You must contact your police department or Sheriff\'s office immediately if you believe a crime is being, or will be, committed. If you have any questions regarding this matter, contact your local police department or county sheriff\'s office.\r\n\r\n5) Scripted or automated access to this site is denied outside of the site\'s rss feed and api. Do not scrape or crawl this site\'s data, the api offered will assure correctness.\r\n\r\n6) Registrants are mapped to the best ability with the data provided, DPS/DCI makes no guarantee of the validity of the mapped locations of registrants.\r\n\r\n=== DISCLAIMER - TERMS AND CONDITIONS ===\r\n\r\nThe State of Iowa and its agencies, officials and employees make no warranty, representation or guaranty as to the content, accuracy, timeliness or completeness of the information provided herein. The State of Iowa, and the Department of Administrative Services, Information Technology Enterprise expressly disclaim any and all liability for any loss or injury caused, in whole or in part, by its actions, omissions, or negligence in procuring, compiling or providing the information contained in this site, including without limitation, liability with respect to any use of this site, or the information contained herein. Reliance on the information contained on this site, is solely at your own risk. The information may change or be altered at any time.\r\n\r\n=== PRIVACY STATEMENT AND POLICY ===\r\n\r\nInformation Collected By Use of This Site:\r\n\r\nPersonally identifiable information which may be collected by use of this site includes IP numbers, date/time, stamps, methods, path, status code and size of request. The information that is available from governmental web sites is subject to these principles and policies:\r\n\r\nAccess to personally identifiable information in public records at state and local levels of government in Iowa is controlled primarily by Chapter 22 of the Code of Iowa. Information generally available under Chapter 22 - and not made confidential elsewhere in the Code of Iowa - may be posted for electronic access.\r\n\r\nPersons concerned with regard to information about them should contact the custodian of the record, which typically is the state agency or other governmental entity that collects and maintains the information.\r\n\r\nThe information collected should only be that necessary to provide the information or services sought by a requester, just as a person might provide such information when visiting a governmental office in person.\r\n\r\nThe information collected is subject to the same controls and uses as that collected by governmental offices visited in person, again subject to the access and confidentiality provisions of Chapter 22, or to other applicable sections of the Code of Iowa. You do not have to provide personal information to visit the web sites or download information. The IP (Internet Protocol) numbers of computers used to visit these sites are noted as part of our statistical analysis on use of our web sites and how to better design services and facilitate access to them. No marketing databases are created nor are any commercial uses made of any such data. Government agencies may request personally identifiable information from you in order to provide requested services, but such information is handled as it would be on an in-person visit to a government office.\r\n\r\nVarious other web sites may be linked through this site. Private sector sites are not subject to Chapter 22. Visitors to those sites may wish to check their privacy statements and be cautious about providing personally identifiable information.\r\n\r\nLinks to Other Sites:\r\n\r\nThis site has links to other web sites as a convenience to our customers. These links may be operated by other government agencies, nonprofit organizations, and private businesses. When you use one of these links you are no longer on this site and this Privacy Statement and Policy will not apply. When you link to another web site, you are subject to the privacy policy of the new site.\r\n\r\nWhen you follow a link to one of these sites neither the State of Iowa, nor any agency, officer, or employee of the State warrants the accuracy, reliability, or timeliness of any information published by the external sites, nor endorses any content, viewpoints, products, or services linked from these systems, and cannot be held liable for any losses caused by use of or reliance on the accuracy, reliability or timeliness of the information. Any person or entity that relies on any information obtained from these systems does so at his or her own risk.\r\n\r\n=== WARRANTIES ===\r\n\r\nTHE INFORMATION CONTAINED ON THIS WEB SITE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT. THE STATE OF IOWA ASSUMES NO RESPONSIBILITY FOR ERRORS OR OMISSIONS IN THIS PUBLICATION OR OTHER DOCUMENTS WHICH ARE REFERENCED BY OR LINKED TO THIS PUBLICATION. REFERENCES TO CORPORATIONS, THEIR SERVICES AND PRODUCTS, ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED. IN NO EVENT SHALL THE STATE OF IOWA BE LIABLE FOR ANY SPECIAL, INCIDENTAL, INDIRECT OR CONSEQUENTIAL DAMAGES OF ANY KIND, OR ANY DAMAGES WHATSOEVER, INCLUDING, WITHOUT LIMITATION, THOSE RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER OR NOT ADVISED OF THE POSSIBILITY OF DAMAGE, AND ON ANY THEORY OF LIABILITY, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS INFORMATION. THIS PUBLICATION COULD INCLUDE TECHNICAL OR OTHER INACCURACIES OR TYPOGRAPHICAL ERRORS. CHANGES ARE PERIODICALLY ADDED TO THE INFORMATION HEREIN; THESE CHANGES WILL BE INCORPORATED IN NEW EDITIONS OF This PUBLICATION.THE STATE OF IOWA MAY MAKE IMPROVEMENTS AND/OR CHANGES IN THE PRODUCT(S) AND/OR THE PROGRAM(S) DESCRIBED IN THIS PUBLICATION AT ANY TIME.\r\n\r\n',
                'captcha': captcha_code,
            }

            response = await self.post('https://www.iowasexoffender.gov/accept/', data=data, follow_redirects=True)
            response.raise_for_status()
            if response.url != "https://www.iowasexoffender.gov/simplesearch/?type=simple&alias=1&action=Submit%20Search":
                logger.error("Captcha is not valid, trying again")
                attempts += 1
                continue

            if not self.total_pages:
                total_pages = re.search(r'There are \d+ items on (\d+) page', response.text)

                if not total_pages:
                    logger.error("Total pages not found while validating session, trying again")
                    attempts += 1
                    continue

                total_pages = total_pages.group(1)
                self.total_pages = int(total_pages)
                logger.success(f"Total pages: {total_pages}")

            return

        raise Exception("Max attempts reached while validating session")


    async def get_offenders_urls(self, page: int):
        params = {
            'alias': '1',
            'type': 'simple',
            'ResultsPaging->SortBy': 'default',
            'ResultsPaging->Page': page,
        }

        try:
            response = await self.get('https://www.iowasexoffender.gov/simplesearch/', params=params, follow_redirects=True)
            if response.status_code == 403:
                logger.warning(f"Got captcha while getting offenders from page {page}, trying again")
                await self.validate_session()
                await self.get_offenders_urls(page)

            else:
                response.raise_for_status()

            page_urls = re.findall(r'<a href="(https?://\S+)" class="resultmap">', response.text)
            logger.info(f"Got {len(page_urls)} offenders urls from page {page}")
            self.offenders_urls.extend(page_urls)

        except Exception as error:
            logger.error(f"Error while getting offenders from page {page}: {error}")


    async def safe_get_offenders_urls(self, page: int):
        async with sem:
            await self.get_offenders_urls(page)


    async def safe_get_offender_data(self, url: str):
        async with sem:
            await self.get_offender_data(url)

    async def get_offender_data(self, url: str):

        def extract_text_or_none(element):
            return element.get_text(strip=True) if element else None

        try:
            response = await self.get(url)
            if response.status_code == 403:
                logger.warning(f"Got captcha while getting offender data from url {url}, trying again")
                await self.validate_session()
                await self.get_offender_data(url)

            else:
                response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            name_element = soup.find("h2", class_="registrant-title")
            name = extract_text_or_none(name_element) if name_element else None

            registration_number_element = soup.find("span", class_="code")
            registration_number = extract_text_or_none(registration_number_element) if registration_number_element else None
            registration_number = re.search('\d+', registration_number).group(0) if registration_number else None

            gender_element = soup.find("div", class_="col-xs-3 col-sm-2", string=lambda text: text and "Gender:" in text)
            gender = extract_text_or_none(gender_element.find_next("div")) if gender_element else None

            race_element = soup.find("div", class_="col-xs-3 col-sm-2", string=lambda text: text and "Race:" in text)
            race = extract_text_or_none(race_element.find_next("div")) if race_element else None

            height_element = soup.find("div", class_="col-xs-3 col-sm-2", string=lambda text: text and "Height:" in text)
            height = extract_text_or_none(height_element.find_next("div")) if height_element else None

            weight_element = soup.find("div", class_="col-xs-3 col-sm-2", string=lambda text: text and "Weight:" in text)
            weight = extract_text_or_none(weight_element.find_next("div")) if weight_element else None

            birthdate_element = soup.find("div", class_="col-xs-3 col-sm-2", string=lambda text: text and "Birthdate:" in text)
            birthdate = extract_text_or_none(birthdate_element.find_next("div")) if birthdate_element else None

            hair_element = soup.find("div", class_="col-xs-3 col-sm-2", string=lambda text: text and "Hair:" in text)
            hair = extract_text_or_none(hair_element.find_next("div")) if hair_element else None

            eyes_element = soup.find("div", class_="col-xs-3 col-sm-2", string=lambda text: text and "Eyes:" in text)
            eyes = extract_text_or_none(eyes_element.find_next("div")) if eyes_element else None

            scars_element = soup.find("legend", string=lambda text: text and "Scars, Marks, Tattoos" in text)
            scars_sub_elements = (
                scars_element.find_next_siblings("strong") if scars_element else None
            )
            scars = ", ".join([
                extract_text_or_none(element) for element in scars_sub_elements
            ]) if scars_sub_elements else None

            address_element = soup.find("legend", string=lambda text: text and "Address" in text)
            address_sub_elements = (
                address_element.find_next_siblings("div", class_="font-weight-bold") if address_element else None
            )
            address = ", ".join([
                extract_text_or_none(element) for element in address_sub_elements
            ]) if address_sub_elements else None

            # address_registered_date_element = soup.find("span", class_="small-updated italics", string=lambda text: text and "Address Registered Date:" in text)
            # print(address_registered_date_element, address_registered_date_element.text)
            # address_registered_date = extract_text_or_none(address_registered_date_element.find_next("strong")) if address_registered_date_element else None

            tier_element = soup.find('legend', string=lambda text: text and 'Tier, Restrictions' in text)
            tier_sub_elements = tier_element.find_next_siblings('div') if tier_element else None

            tier = extract_text_or_none(tier_sub_elements[0].find_next('a')) if tier_sub_elements and len(tier_sub_elements) >= 2 else None
            residency = extract_text_or_none(tier_sub_elements[1].find_next('strong')) if tier_sub_elements and len(tier_sub_elements) >= 2 else None
            exclusion = extract_text_or_none(tier_sub_elements[2].find_next('a')) if tier_sub_elements and len(tier_sub_elements) >= 3 else None
            employment = extract_text_or_none(tier_sub_elements[3].find_next('a')) if tier_sub_elements and len(tier_sub_elements) >= 4 else None

            if registration_number:
                await OffendersData.add_offender(
                    registration_number=int(registration_number),
                    name=name,
                    race=race,
                    gender=gender,
                    birthdate=birthdate,
                    height=height,
                    weight=weight,
                    hair_color=hair,
                    eye_color=eyes,
                    scars=scars,
                    address=address,
                    tier=tier,
                    residency=residency,
                    exclusion=exclusion,
                    employment=employment,
                )

        except Exception as error:
            logger.error(f"Error while getting offender data from url {url}: {error}")

    async def process_offenders_urls(self) -> None:
        tasks = []
        for page in range(1, self.total_pages + 1):
            tasks.append(asyncio.create_task(self.safe_get_offenders_urls(page)))

        await asyncio.gather(*tasks)
        logger.success(f"Got {len(self.offenders_urls)} offenders urls | Start processing offenders data")


    async def process_offenders_data(self) -> None:
        tasks = []
        for url in self.offenders_urls:
            tasks.append(asyncio.create_task(self.safe_get_offender_data(url)))

        await asyncio.gather(*tasks)


    async def start(self) -> None:
        start_time = datetime.now()
        try:
            logger.success("Scraper started")
            await self.validate_session()
            await self.process_offenders_urls()
            await self.process_offenders_data()
            logger.success(f"Scraper finished | Total offenders: {len(self.offenders_urls)} | Execution time: {datetime.now() - start_time}")

        except Exception as error:
            logger.error(f"Error while starting scraper: {error}")

        await self.aclose()
        return
