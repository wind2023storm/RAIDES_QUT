import os
import re
from enum import Enum
from typing import Dict, Union, Tuple, List

import pandas as pd
from bs4 import BeautifulSoup as BS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from main.utils.django_date import try_get_datetime
from tms.models import Tenement, TenementHolder, QLDTenementBlock, PermitStatusChoices, QLDEnvironmentalAuthority
from tms.models.models import EnviroPermitStateChoices

# from tms.models import Tenement, TenementHolder, SubBlock, Block, PermitTypeChoices, PermitStatusChoices, \
#     EnviroPermitStateChoices, BlockBimChoices

"""
How to scrape a tenement from the web:

permit_type = 'EPM'
permit_number = '28118'
driver_path = os.path.join(os.path.abspath(''),'geckodriver.exe') # path of driver

url = get_tenement_url(permit_type, permit_number)
src = try_get_html(url, driver_path, save=True)
tables = scrape_tables(src)

NOTE: 
    Scraping functions are specific to:
        - myminesonlineservices.business.qld.gov.au
        - des.qld.gov.au   
"""


# Dataset of EA's
# TODO: have this url in the same cron job as the FTP server downloads as this needs to be updated regularly also
# https://storagesolutiondocsprod.blob.core.windows.net/register-documents-ea/ea-register.xlsx


class DriverType(Enum):
    """Driver type for use in ``Selenium``, download one of the following depending on what browser you have installed:

    - Firefox Web Driver (geckodriver): https://github.com/mozilla/geckodriver/releases
    - Chrome Web Driver (chromedriver): https://chromedriver.chromium.org/downloads
    """
    FIREFOX = 1
    CHROME = 2


DRIVER_PATH = os.path.join(os.path.abspath('pwc/utils/'), 'geckodriver.exe')
DRIVER_TYPE = DriverType.FIREFOX

SCRAPER_DEBUG_MODE = True


def try_find_choice(cls, key):
    """Finds a choice from a value, can either be the key or label of a choice

    Parameters
    ----------
        cls : Choice Model
            A TextChoices model
        key : str
            Key to find
    """
    name, label = tuple(zip(*cls.choices))

    if key in name:
        return cls[key].value

    if key in label:
        choices = dict(zip(label, name))
        return cls(choices[key]).value

    return None


def get_tenement_url(permit_type: str, permit_number) -> Tuple[str, str]:
    """Just returns the url with the attributes filled out"""
    url = f'https://myminesonlineservices.business.qld.gov.au/Web/PublicEnquiryReport.htm?permitType={permit_type}&permitNumber={permit_number}'
    xpath = '//div[@data-bind="text: permitNO"]'
    return url, xpath


# def get_environmental_url(permit_type: str, permit_number: str) -> Tuple[str, List[str]]:
#     """Returns the populated url query for an Environmental Authority seach"""
#     url = f'https://apps.des.qld.gov.au/public-register/results/ea.php?location={permit_type}{permit_number}'
#     xpath = ['//td[@class="sorting_1"]/a', '//div[@class="details"]']
#     return url, xpath


def get_environmental_url(permit_type: str, permit_number) -> Tuple[str, List[str]]:
    """Using the ea-register.xlsx we can get the ea_reference. We use the Excel spreadsheet as searching
    by the tenement permit id is unreliable and often returns the wrong result."""
    # Load the EA-data
    excel_path = os.path.join(os.getcwd(), 'tms/utils/ea_data/', 'ea-register.xlsx')
    df = pd.read_excel(excel_path)

    # Search the locations column for the permit id we're looking for
    permit_id = f'{permit_type}{permit_number};'
    row = df[df['Locations'].str.contains(permit_id).fillna(False)]['Permit Reference']

    # Get the ea reference nuber from the reference column
    ea_reference = row.values[0]

    # Compile URL and xpaths
    url = f'https://apps.des.qld.gov.au/public-register/results/ea.php?reference={ea_reference}'
    xpath = ['//td[@class="sorting_1"]/a', '//div[@class="details"]']
    return url, xpath


def format_string(string) -> str:
    """Removes punctuation and Capitalizes each word"""
    return re.sub(r'[^A-Za-z0-9]+', '', string.title())


def open_browser(driver_path, driver_type):
    """Opens a headless browser using Selenium

    Parameters
    ----------
    driver_path : str
        System path to the driver
    driver_type : DriverType
        Type of driver being used

    Returns
    -------
        browser : WebDriver
            Browser that was opened
    """
    # Set up headless browser based on selected driver type
    if driver_type == DriverType.FIREFOX:
        from selenium.webdriver.firefox.service import Service
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')

        browser = webdriver.Firefox(options=options, service=Service(driver_path))
    elif driver_type == DriverType.CHROME:
        from selenium.webdriver.chrome.service import Service
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')

        browser = webdriver.Chrome(options=options, service=Service(driver_path))
    else:
        raise ValueError("Incorrect driver_type. Must be FIREFOX or CHROME.")

    return browser


def try_get_website(browser, url: str, xpath: str):
    """Attempts to navigate to a website from a start url. Supplied xpaths indicate elements 'clicked' to reach desired
    location.

    Parameters
    ----------
        browser : WebDriver
            Browser used during the operation, use `open_browser()` function. Must be closed manually.
        url : str
            URL of start website
        xpath : str, list
            XPATH to search for. If list is provided, it is assumed that the first N-1 elements are links that
            are to be clicked
        debug : bool
            Whether to print out some debug information at runtime

    Returns
    -------
        success : bool
            Whether or not the function was able to navigate completely.
    """
    # For looping purposes if the xpath supplied is a string, turn it into a list
    if isinstance(xpath, str):
        xpath = [xpath]

    path_count = len(xpath)

    if SCRAPER_DEBUG_MODE:
        print(f'try_get_website({browser}, {url}, {xpath})')

    # Should the browser be unable to locate the target xpath element, WebDriverWait will throw an exception
    browser.get(url)

    # Iterate list of xpaths in the case we need to find a page through other pages
    for i, path in enumerate(xpath):
        if SCRAPER_DEBUG_MODE:
            print(f"LOADING {i + 1}/{path_count}:", url)

        _xpath = (By.XPATH, path)
        element = WebDriverWait(browser, 30).until(EC.visibility_of_element_located(_xpath))

        if not element:
            raise Exception('Page not found')

        # If we have more than one xpath, click the element to navigate to the next page
        if i < path_count - 1:
            url = element.get_property('href')
            element.click()

    if SCRAPER_DEBUG_MODE:
        print('Success!')
    return True


def scrape_tenement_data(browser, permit_type, permit_number) -> Union[Dict[str, any], None]:
    """Attempts to scrape un-formatted data from 'myminesonline', thankfully we can use the websites API to avoid
    any manual scraping with beautiful soup.

    Parameters
    ----------
        browser : WebDriver
            Browser used during the operation, use `open_browser()` function. Must be closed manually.
        permit_type : str
            Tenement permit type e.g., 'EPM'
        permit_number : str
            Tenement permit number

    Returns
    -------
        dict[str, any] or None
            The dictionary containing the tenement data, if nothing was found, data will be empty
    """
    try:
        # Just navigate to the page, couldn't be bothered duplicating code
        try_get_website(browser, *get_tenement_url(permit_type, permit_number))

        return browser.execute_script('return $.getJSON(apiRequest, function (jsonData) {});')
    except Exception as e:
        print('Could not Scrape', e)
        return None


def scrape_environmental_data(browser, permit_type: str, permit_number: str) -> Dict[str, any]:
    """Attempts to scrape un-formatted data from the Environmental Authority tables, it's possible that multiple locations
    or holders exist for any permit. Make sure to check for these

    Parameters
    ----------
        browser : WebDriver
            Browser used during the operation, use `open_browser()` function. Must be closed manually.
        permit_type : str
            Tenement permit type e.g., 'EPM'
        permit_number : str
            Tenement permit number

    Returns
    -------
        data : dict[str, any]
            The dictionary containing the environmental association data, if nothing was found, data will be empty
    """
    try:
        try_get_website(browser, *get_environmental_url(permit_type, permit_number))

        # Scrape permit data from the page source
        soup = BS(browser.page_source, 'html.parser')
        data = {}

        # Get Primary details container
        main = soup.find('div', {'class': 'details'})

        # Permit ID
        data['PermitID'] = re.match(r"(?:Details of permit )(.+)", main.find('h2').text)[1]

        # Loop the two tables
        for table in main.find_all('table', {'class': 'table'}):

            # Only the activity table has a head
            if table.find('thead'):
                # This is the Activity table (we need this to confirm the EPM we're looking for exists here)
                thead = table.find('thead').find_all('th', {'class': 'w-50'})
                tbody = table.find('tbody').find_all('td')

                # Zip the head and body together, so we can loop connected elements
                for (h, d) in zip(thead, tbody):
                    th = format_string(h.text)
                    td = re.sub(r"[ \n]+", " ", d.text).strip()

                    # We may have multiple locations that will need to be checked
                    if th == 'Location':
                        td = [x for x in td.split(' ')]

                    data[th] = td
            else:
                # This is the primary details e.g., Permit Type, Condition, Date, Holder
                for row in table.find_all('tr'):
                    th = format_string(row.find('td', {'class': 'w-25'}).text)
                    td = row.find('td', {'class': None}).text.strip()

                    data[th] = td

        return data

    except Exception as e:
        print('scrape_environmental_data error:', e)
        pass

    return {}


def scrape_tenement(permit_state, permit_type, permit_number) -> Tuple[Tenement, bool]:
    """ Attempts to update an existing Tenement or create a new one in the database.

    Parameters
    ----------
    state : str
        TODO: Make this useful for other states, currently only QLD does anything
        Permit State e.g., QLD, NSW, WA
    permit_type : str
        Permit type e.g., EPM or MDL
    permit_number
        The permit number
    project : Project, optional
        The project in which the tenement is assigned

    Returns
    -------
        result : Tenement, bool
            None if Tenement wasn't scraped or a tuple of Tenement and True if it was created and False otherwise
    """
    if permit_state != 'QLD':
        raise ValueError("Only QLD Tenements are supported at this time.")

    # Open the browser
    browser = open_browser(DRIVER_PATH, DRIVER_TYPE)

    # Begin scraping
    tenement_data = scrape_tenement_data(browser, permit_type, permit_number)

    if tenement_data:
        ea_data = scrape_environmental_data(browser, permit_type, permit_number)
    else:
        ea_data = None

    # Close the headless browser as it's no longer needed
    browser.quit()

    # Have to do this here because we need to close the browser before we return
    if not tenement_data:
        return None, False

    # Pull subsections of the data for easier indexing, set default to an empty dict to handle type errors later on
    permit_info = tenement_data.get('PermitSection', {})
    native_title = tenement_data.get('NativeTitleSection', {})
    holder_info = tenement_data.get('HoldersSection', {})
    area = tenement_data.get('AreaSection', {})
    purpose_minerals = tenement_data.get('PurposeAndMineralsSection', {})
    financials = tenement_data.get('FinancialsSection', {})
    ahr_info = holder_info.get('AHR', {})
    area_details = area.get('AreaDetails', {})

    # The scraped json data needs to be formatted according to the tenement model fields
    # Update or Create the Tenement
    tenement, was_created = Tenement.objects.update_or_create(
        permit_state=permit_state,
        permit_type=permit_type,
        permit_number=permit_number,
        defaults={
            'permit_name': permit_info.get('PermitName'),
            'permit_status': try_find_choice(PermitStatusChoices, permit_info.get('PermitStatusTypeDescription')),

            'date_lodged': try_get_datetime(permit_info.get('DateLodged')),
            'date_granted': try_get_datetime(permit_info.get('ApproveDate')),
            'date_commenced': try_get_datetime(permit_info.get('CommenceDate')),
            'date_expiry': try_get_datetime(permit_info.get('ExpiryDate')),
            'date_renewed': None,  # try_get_datetime(permit_info.get('ExpiryDate')),

            'ahr_name': ahr_info.get('Name'),
            'ahr_address': ahr_info.get('Address'),
            'ahr_email': ahr_info.get('Email'),
            'ahr_mobile_number': ahr_info.get('MobilePhone'),
            'ahr_phone_number': ahr_info.get('Phone'),

            'area_units': area_details.get('Area', {}).get('Area', None),
            'area_label': area_details.get('Area', {}).get('Unit', None),
            'area_exclusions': area_details.get('Exclusions'),
            'area_locality': area_details.get('Locality'),
            'area_local_authority': area_details.get('LocalAuthority'),
            'area_mining_district': area_details.get('MiningDistrict'),

            'prescribed_minerals': [
                # The prescribed minerals are in a weird nested dict, lets consolidate them into a simple list
                sub[key] for sub in purpose_minerals.get('SoughtMinerals', {}).get('Minerals', [])
                for key in sub
            ],
            'rent_rate': financials.get('RentRate'),

            'native_title_description': None,  # native_title.get('Description'),
            'native_title_outcome': None,  # native_title.get('Outcome'),
            'native_title_parties': None,  # native_title.get('Parties'),
            'native_title_process': native_title.get('CurrentNT'),
            # 'native_title_date_start': None,  # native_title.get('StartDate'),

        })

    # If the tenement was updated, deleted the previous blocks/holders just in case some were removed etc.
    if not was_created:
        tenement.blocks.all().delete()
        tenement.holders.all().delete()
        
    # EA Info time, first we need to make sure the scraped EA contained the tenement we're looking for
    if ea_data and permit_type + str(permit_number) in ea_data.get('Location', []):
        print(ea_data)
        QLDEnvironmentalAuthority.objects.update_or_create(
            tenement=tenement,
            number=ea_data.get('PermitID'),
            defaults={
                'type': ea_data.get('PermitType'),
                'condition_type': ea_data.get('ConditionType'),
                'activity': ea_data.get('Activity'),
                'status': try_find_choice(EnviroPermitStateChoices, ea_data.get('Status')),
                'holder': ea_data.get('PermitHolderS'),
                'date_effective': try_get_datetime(ea_data.get('EffectiveDate')),
                'assurance': 0,  # TODO: Figure out how to get this
            }
        )

    # Start adding the new holders
    for holder in holder_info.get('Holders', []):
        TenementHolder.objects.create(
            tenement=tenement,
            acn=holder.get('Acn'),
            address=holder.get('Address'),
            change=holder.get('Change'),
            status=try_find_choice(TenementHolder.StatusChoices, holder.get('Status')),
    
            date_of_birth=try_get_datetime(holder.get('Dob')),
            date_start=try_get_datetime(holder.get('StartDate')),
            date_end=try_get_datetime(holder.get('EndDate')),
    
            is_authorised_holder=True if holder.get('IsAuthorisedHolder') else False,
            name_main=holder.get('MainName'),
            name_other=holder.get('OtherNames'),
            permit_role_type=holder.get('PermitRoleTypeDescription'),
            tenancy_type_description=holder.get('TenancyTypeDescription'),
            share_percent=holder.get('SharePercent'),
        )

    # Add blocks/subblocks
    for block in area.get('SubBlocks', []):
        # Copy the default dictionary
        sub_blocks = QLDTenementBlock.default_subblocks
        sub_blocks.update(dict.fromkeys(block.get('SubBlockList', '').split(','), True))

        QLDTenementBlock.objects.create(
            tenement=tenement,
            block_identification_map=try_find_choice(QLDTenementBlock.BIMChoices, block.get('Name')),
            number=block.get('BlockNo'),
            sub_blocks=sub_blocks,
        )

    # Have to get the object again since some fields aren't update correctly (namely the date fields haven't been
    # converted from datetime until after the object is created)
    return Tenement.objects.get(permit_type=permit_type, permit_number=permit_number), was_created

# def scrape_tenement(permit_state, permit_type, permit_number) -> [Tenement, bool]:
#     """ Attempts to update an existing Tenement or create a new one in the database.
#
#     Parameters
#     ----------
#     state : str
#         TODO: Make this useful for other states, currently only QLD does anything
#         Permit State e.g., QLD, NSW, WA
#     permit_type : str
#         Permit type e.g., EPM or MDL
#     permit_number
#         The permit number
#     project : Project, optional
#         The project in which the tenement is assigned
#
#     Returns
#     -------
#         result : Tenement, bool
#             None if Tenement wasn't scraped or a tuple of Tenement and True if it was created and False otherwise
#     """
#     if state != 'QLD':
#         raise ValueError("Scraping only handles QLD Tenements at this time.")
#
#     # Open the browser
#     browser = open_browser(DRIVER_PATH, DRIVER_TYPE)
#
#     # Begin scraping
#     tenement_data = scrape_tenement_data(browser, permit_type, permit_number)
#
#     if tenement_data:
#         ea_data = scrape_environmental_data(browser, permit_type, permit_number)
#
#     # Close the headless browser as it's no longer needed
#     browser.quit()
#
#     # Have to do this here because we need to close the browser before we return
#     if not tenement_data:
#         return None, False
#
#     # Pull subsections of the data for easier indexing, set default to an empty dict to handle type errors later on
#     permit_info = tenement_data.get('PermitSection', {})
#     native_title = tenement_data.get('NativeTitleSection', {})
#     holder_info = tenement_data.get('HoldersSection', {})
#     area = tenement_data.get('AreaSection', {})
#     purpose_minerals = tenement_data.get('PurposeAndMineralsSection', {})
#     financials = tenement_data.get('FinancialsSection', {})
#     ahr_info = holder_info.get('AHR', {})
#     area_details = area.get('AreaDetails', {})
#
#     # The scraped json data needs to be formatted according to the tenement model fields
#     tenement_dict = {
#         'state': state,
#         'permit_type': try_find_choice(PermitTypeChoices, permit_type),
#         'permit_number': permit_number,
#         'permit_status': try_find_choice(PermitStatusChoices, permit_info.get('PermitStatusTypeDescription')),
#         'date_lodged': try_get_datetime(permit_info.get('DateLodged')),
#         'date_grant': try_get_datetime(permit_info.get('ApproveDate')),
#         'date_commenced': try_get_datetime(permit_info.get('CommenceDate')),
#         'date_expiration': try_get_datetime(permit_info.get('ExpiryDate')),
#
#         'authorised_holder_name': ahr_info.get('Name'),
#         'authorised_holder_address': ahr_info.get('Address'),
#
#         'native_title_current_process': native_title.get('CurrentNT'),
#
#         'mining_district': area_details.get('MiningDistrict'),
#         'local_authority': area_details.get('LocalAuthority'),
#         'mining_exclusions': area_details.get('Exclusions'),
#
#         # The prescribed minerals section is a bit wacky so some list comprehension was necessary
#         'prescribed_minerals': ', '.join(
#             [sub[key] for sub in purpose_minerals.get('SoughtMinerals', {}).get('Minerals', [])
#              for key in sub]),
#
#         'financial_area': area_details.get('Area', {}).get('Area', None),
#         'financial_rent': financials.get('RentRate'),
#     }
#
#     # EA Info time, first we need to make sure the scraped EA contained the tenement we're looking for
#     if ea_data and f"{permit_type}{permit_number}" in ea_data.get('Location', []):
#         tenement_dict = dict(tenement_dict, **{
#             'ea_number': ea_data.get('PermitID'),
#             'ea_type': ea_data.get('PermitType'),
#             'ea_condition_type': ea_data.get('ConditionType'),
#             'ea_activity': ea_data.get('Activity'),
#             'ea_status': try_find_choice(EnviroPermitStateChoices, ea_data.get('Status')),
#             'ea_holder': ea_data.get('PermitHolderS'),
#             'ea_effective_date': try_get_datetime(ea_data.get('EffectiveDate')),
#             'ea_assurance': 0,
#         })
#
#     # Update or Create the Tenement
#     tenement, was_created = Tenement.objects.update_or_create(
#         permit_type=permit_type,
#         permit_number=permit_number,
#         defaults=tenement_dict,
#     )
#
#     # If the tenement was updated, deleted the previous blocks/holders just in case some were removed etc.
#     if not was_created:
#         tenement.blocks.all().delete()
#         tenement.holders.all().delete()
#
#     # Start adding the new holders
#     for holder in holder_info.get('Holders', []):
#         holder_object = TenementHolder(**{
#             'tenement': tenement,
#             'name': holder.get('MainName'),
#             'share': holder.get('SharePercent'),
#             'held_from': try_get_datetime(holder.get('StartDate')),
#             'held_to': try_get_datetime(holder.get('EndDate')),
#             'is_authorised_holder': True if holder.get('IsAuthorisedHolder') else False
#         })
#         holder_object.save()
#
#     # Add blocks/subblocks
#     for block in area.get('SubBlocks', []):
#         block_object = Block(**{
#             'tenement': tenement,
#             'block_identification_map': try_find_choice(BlockBimChoices, block.get('Name')),
#             'number': block.get('BlockNo'),
#         })
#         block_object.save()
#
#         for sub_block in block.get('SubBlockList', '').split(','):
#             sub_block_object = SubBlock(**{
#                 'block': block_object,
#                 'number': sub_block,
#                 'status': 'G',
#             })
#             sub_block_object.save()
#
#     # Have to get the object again since some fields aren't update correctly (namely the date fields havent been
#     # converted from datetime until after the object is created)
#     return Tenement.objects.get(permit_type=permit_type, permit_number=permit_number), was_created


# def scrape_tenement_tables(html: str) -> Union[Dict[str, pandas.DataFrame], None]:
#     """Attempts to scrape html data into pandas dataframes.
#
#     Can work on tables of types::
#
#         div>.dataTable
#         table
#         div>.table
#         div>.sectionTitle (Some weird way to make tables idk why)
#
#     Parameters
#     ----------
#         html : str
#             HTML as a string
#
#     Returns
#     -------
#         tables : dict[str, pandas.DataFrame]
#             dictionary containing scraped tables where key is the name of the table.
#     """
#     if html is None:
#         return None
#
#     soup = BS(html, 'html.parser')
#     tables = {}
#
#     # The website has its tables nested under these accordion type menus, using regex is the only way to get
#     # them all as it's the only consistent value across all of them.
#     for menu_item in soup.find_all('div', {'class': re.compile(r'.*ui-accordion-content.*')}):
#
#         for dt in menu_item.find_all(True, {'class': ['dataTable']}):
#             values = []
#             labels = []
#             t_type = None
#
#             # Disgusting attempt at finding the tables title, we have to store by name as some tenements
#             # won't have certain tables due to either lack of content or differing tenement type.
#             try:
#                 t_title = dt.find('div', {'class': 'sectionTitle'}).text
#             except AttributeError:
#                 try:
#                     t_title = menu_item.parent.find('h3', re.compile('.*ui-accordion-header.*')).text
#                 except AttributeError:
#                     t_title = None
#
#             # DataTable
#             if dt.find('div', {'class': 'dataField'}):
#                 t_type = 'dataTable'
#                 labels = [x.text for x in dt.find_all('div', {'class': 'label'})]
#                 values = [[x.text for x in dt.find_all('div', {'class': 'value'})]]
#
#             # Regular Table
#             elif dt.find('table') and not dt.find('div', {'class': 'table'}):
#                 t_type = 'table'
#                 labels = [x.text for x in dt.find_all('th')]
#                 values = []
#                 for row in dt.find_all('tr'):
#                     r = [x.text for x in row.find_all('td')]
#                     if len(r) > 0:
#                         values.append(r)
#
#             # Div Table (where the table is defined by div classes)
#             elif dt.find('div', {'class': 'table'}):
#                 t_type = 'divTable'
#                 labels = [x.text for x in dt.find_all('div', {'class': 'th'})]
#                 values = [[x.text for x in dt.find_all('div', {'class': 'td'})]]
#
#                 # Weird way to make a table
#             elif dt.find('div', {'class': 'sectionTitle'}):
#                 t_type = 'sectionTable'
#                 labels = [x.text for x in dt.find_all('div', {'class': 'sectionTitle'})]
#                 values = [x.text for x in dt.find_all('div', {'class': 'sectionBody'})]
#
#             # Store it if it's actually a real life table
#             if t_type is not None:
#                 labels = [format_string(x) for x in labels]
#                 df = pd.DataFrame(data=values, columns=labels)
#
#                 t = format_string(t_title)
#                 if t in tables.keys():
#                     t = t + '1'
#
#                 tables[t] = df
#
#     return tables


# def scrape_tenement_old(permit_type, permit_number, project=None) -> [Tenement, bool]:
#     """ Attempts to update an existing Tenement or create a new one in the database.
#
#     Parameters
#     ----------
#     permit_type : str
#         Permit type e.g., EPM or MDL
#     permit_number
#         The permit number
#     project : Project, optional
#         The project in which the tenement is assigned
#
#     Returns
#     -------
#         result : Tenement, bool
#             None if Tenement wasn't scraped or a tuple of Tenement and True if it was created and False otherwise
#     """
#     # Open the browser
#     browser = open_browser(DRIVER_PATH, DRIVER_TYPE)
#
#     # Scrape Tenement
#     url, xpath = get_tenement_url(permit_type, permit_number)
#     tenement_source = try_get_html(url, browser, xpath, debug=True)
#     tenement_tables = scrape_tenement_tables(tenement_source)
#
#     if not tenement_tables:
#         browser.quit()
#         return None, False
#
#     # Scrape Environmental Authority
#     url, xpath = get_environmental_url(permit_type, permit_number)
#     enviro_source = try_get_html(url, browser, xpath, debug=True)
#     enviro_table = scrape_enviro_table(enviro_source)
#
#     # Have to quit the browser else it'll just live in memory forever
#     browser.quit()
#
#     permit_details = tenement_tables["PermitDetails"].iloc[0, :]
#     native_title = tenement_tables['NativeTitle'].iloc[0, :]
#     native_title1 = tenement_tables['NativeTitle1'].iloc[0, :]
#     prescribed_minerals = tenement_tables['PurposeAndMinerals'].iloc[0, :]
#     financial_details = tenement_tables['RentDetails'].iloc[0, :]
#     block_details = tenement_tables['SubBlocks']
#     area_details = tenement_tables['Area'].iloc[0, :]
#     authorised_holder_representative = tenement_tables['AuthorisedHolderRepresentativeAhr']
#     holder_details = tenement_tables['Holders']
#
#     # Start building the Tenement Model, match the table contents against Tenement Model fields
#     tenement_dict = {
#         'project': project,
#         'permit_type': try_find_choice(PermitTypeChoices, permit_type),
#         'permit_number': permit_number,
#         'permit_status': try_find_choice(PermitStatusChoices, permit_details['Status']),
#         'date_lodged': try_get_datetime(permit_details['LodgedDate']),
#         'date_grant': try_get_datetime(permit_details['GrantDate']),
#         'date_commenced': try_get_datetime(permit_details['CommencementDate']),
#         'date_expiration': try_get_datetime(permit_details['ExpiryDate']),
#
#         'authorised_holder_name': authorised_holder_representative.iloc[0, 0],
#         'authorised_holder_address': authorised_holder_representative.iloc[1, 0],
#
#         'native_title_current_process': native_title.get('CurrentProcess', None),
#         'native_title_description': native_title.get('Description', None),
#         'native_title_outcome': native_title1.get('Outcome', None),
#         'native_title_process': native_title1.get('Process', None),
#
#         'prescribed_minerals': prescribed_minerals['PrescribedMinerals'],
#
#         'financial_area': financial_details['AreaUnits'],
#         'financial_rent': float(financial_details['RateUnitArea'].replace('$', '')),
#
#         'mining_district': area_details['MiningDistrict'],
#         'local_authority': area_details['LocalAuthority'],
#         'mining_exclusions': area_details['Exclusions'],
#     }
#
#     # EA Info time, first we need to make sure the scraped EA contained the tenement we're looking for
#     enviro_dict = {}
#     if enviro_table:
#         if f"{permit_type}{permit_number}" in enviro_table.get('Location', []):
#             enviro_dict = {
#                 'ea_number': enviro_table.get('PermitID', None),
#                 'ea_type': enviro_table.get('PermitType'),
#                 'ea_condition_type': enviro_table.get('ConditionType', None),
#                 'ea_activity': enviro_table.get('Activity', None),
#                 'ea_status': try_find_choice(EnviroPermitStateChoices, enviro_table.get('Status')),
#                 'ea_holder': enviro_table.get('PermitHolderS', None),
#                 'ea_effective_date': try_get_datetime(enviro_table.get('EffectiveDate', None)),
#                 'ea_assurance': 0,
#             }
#
#     # Update or Create the Tenement defaults are concatenated dicts we built just before
#     tenement, was_created = Tenement.objects.update_or_create(
#         permit_type=permit_type,
#         permit_number=permit_number,
#         defaults={**tenement_dict, **enviro_dict})
#
#     # Delete previous blocks and holders in case they were changed by the update
#     if not was_created:
#         tenement.blocks.all().delete()
#         tenement.holders.all().delete()
#
#     for row in range(len(holder_details.index)):
#         series = holder_details.iloc[row, :]
#
#         holder = TenementHolder(**{
#             'tenement': tenement,
#             'name': series['HolderName'],
#             'share': series['Share'],
#             'held_from': try_get_datetime(series['HeldFrom']),
#             'held_to': try_get_datetime(series['HeldTo']),
#             'is_authorised_holder': series['AuthorisedHolder'] == 'Yes'
#         })
#         holder.save()
#
#     for row in range(len(block_details.index)):
#         series = block_details.iloc[row, :]
#
#         block = Block(**{
#             'tenement': tenement,
#             'block_identification_map': try_find_choice(BlockBimChoices, series['Bim']),
#             'number': series['Block']
#         })
#         block.save()
#
#         for x in list(filter(None, series.iloc[2:].to_list())):
#             sub_block = SubBlock(**{
#                 'block': block,
#                 'number': x,
#                 'status': 'G'
#             })
#             sub_block.save()
#
#     return Tenement.objects.get(permit_type=permit_type, permit_number=permit_number), was_created


# def try_get_html(url: str, browser, xpath: str, save_filename='out.html', save=False, debug=False):
#     """Attempts to gather the HTML source from a website using a FireFox driver.
#     To pull all html after javascript has run, set XPATH to a field that would be
#     visible after the fact.
#
#     Important
#     ---------
#         Browser must be closed manually after, it is left open for consecutive calls of this function.
#
#     Parameters
#     ----------
#         url : str
#             URL to get source from
#         browser : str
#             Browser used to scrape, use `open_browser()` function. Must be closed manually.
#         xpath : str, list
#             XPATH to search for. If list is provided, it is assumed that the first N-1 elements are links that are to be clicked.
#         save : bool, optional
#             Whether to save the source to file (default: False)
#         save_filename : str, optional
#             Filename to save as (default: out.html)
#         debug : bool
#             Whether to print out debug statements e.g., LOADING PAGE a/b
#
#     Returns
#     -------
#         html: str or None
#             HTML Source of webpage
#     """
#     if isinstance(xpath, str):
#         xpath = [xpath]
#
#     if debug:
#         print(f"LOADING {1}/{len(xpath)}:", url)
#
#     browser.get(url)
#     src = None
#
#     try:
#         # Wait for a specific element to be visible before proceeding.
#         for i, path in enumerate(xpath):
#             _xpath = (By.XPATH, path)
#             element = WebDriverWait(browser, 10).until(EC.visibility_of_element_located(_xpath))
#             src = browser.page_source
#
#             if i < len(xpath) - 1:
#                 if debug:
#                     print(f"LOADING {i + 2}/{len(xpath)}:", element.get_property('href'))
#                 element.click()
#
#         # Save it to a file for debugging if necessary
#         if save:
#             with open(save_filename, 'w', encoding='utf8') as output:
#                 output.write(str(src))
#
#         if debug:
#             print("Success!")
#     except Exception as e:
#         if debug:
#             print("UNABLE TO LOCATE XPATH ELEMENT", e)
#     finally:
#         # Make sure to close the browser
#         return src
