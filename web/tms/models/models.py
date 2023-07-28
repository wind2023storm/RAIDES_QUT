import uuid
from datetime import datetime
from typing import Union, Dict, Any, List, Tuple

import django.core.validators as validators
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.contrib.postgres import fields
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.db import models
from django.db.models import Sum, QuerySet
from django.urls import reverse
from django.utils.text import slugify
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _

from main.utils import django_date
from main.utils.fields import ChoicesLabelCase
from media_file.models import MediaFile
from project.models import Project, AustraliaStateChoices
from tms.models.model_choices import PermitTypeChoices, PermitStatusChoices, EnviroPermitStateChoices
from tms.managers import TenementManager, TaskManager

User = get_user_model()




# 25 sub-blocks ignoring I
SUBBLOCK_CHOICES = tuple((str(i + 1), v) for i, v in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ') if v != 'I')


class Tenement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, related_name='tenements', blank=True, null=True, on_delete=models.SET_NULL)

    # PERMIT ID SECTION
    permit_state = models.CharField(choices=AustraliaStateChoices.choices, max_length=3)
    permit_type = models.CharField(choices=PermitTypeChoices.choices(), max_length=10)
    permit_number = models.IntegerField()
    permit_name = models.CharField(max_length=256, null=True, blank=True)
    permit_status = models.CharField(choices=PermitStatusChoices.choices, max_length=2)

    # DATE SECTION
    date_lodged = models.DateField()
    date_granted = models.DateField(null=True, blank=True)
    date_commenced = models.DateField(null=True, blank=True)
    date_expiry = models.DateField(null=True, blank=True)
    date_renewed = models.DateField(null=True, blank=True)  # It appears this field has some relation to the current term calculations

    # AUTHORISED HOLDER REPRESENTATIVE SECTION
    ahr_name = models.CharField(max_length=256, null=True, blank=True)
    ahr_address = models.CharField(max_length=256, null=True, blank=True)
    ahr_email = models.EmailField(null=True, blank=True)
    ahr_mobile_number = models.CharField(max_length=32, null=True, blank=True)
    ahr_phone_number = models.CharField(max_length=32, null=True, blank=True)

    # AREA SECTION
    area_units = models.FloatField(null=True, blank=True)
    area_label = models.CharField(max_length=256, null=True, blank=True)  # The area units metric label e.g., Sub Blocks or Hectares
    area_exclusions = models.CharField(max_length=1024, null=True, blank=True)
    area_locality = models.CharField(max_length=256, null=True, blank=True)
    area_local_authority = models.CharField(max_length=256, null=True, blank=True)
    area_mining_district = models.CharField(max_length=256, null=True, blank=True)
    area_polygons = models.MultiPolygonField(null=True, blank=True)  # Polygonal coordinates of the tenement, not sure if this is capable

    # MISC SECTION
    prescribed_minerals = fields.ArrayField(models.CharField(max_length=64), blank=True, null=True)
    rent_rate = models.FloatField(null=True, blank=True)

    # NATIVE TITLE SECTION
    native_title_description = models.CharField(max_length=256, null=True, blank=True)
    native_title_outcome = models.CharField(max_length=256, null=True, blank=True)
    native_title_parties = models.CharField(max_length=256, null=True, blank=True)
    native_title_process = models.CharField(max_length=256, null=True, blank=True)

    objects = TenementManager()

    @property
    def permit_id(self) -> str:
        return f'{self.permit_type} {self.permit_number}'

    def get_permit_type_display(self):
        return PermitTypeChoices.get_display(self.permit_state, self.permit_type)

    def get_absolute_url(self):
        return reverse('tms:dashboard', kwargs={
            'permit_state': self.permit_state,
            'permit_type': self.permit_type,
            'permit_number': self.permit_number})

    def file_directory(self):
        """This path is used for storing media files using the MediaFile object"""
        return f'{self.project.file_directory()}/tms/{self.permit_state}-{self.permit_type}-{self.permit_number}'

    @property
    def date_current_start(self) -> Union[datetime.date, None]:
        """Often the `date_renewed` stands as the precedent for other date calculations. If the permit is yet to be
        renewed just return the `date_approved` or None if neither exist."""
        # if self.date_renewed:
        #     return self.date_renewed
        if self.date_granted:
            return self.date_granted

        return None

    @property
    def term_cumulative(self) -> Union[int, None]:
        """Total number of terms permitted starting from initial `date_approved` ending `date_expiry`"""
        if self.date_granted and self.date_expiry:
            return relativedelta(self.date_expiry, self.date_granted).years + 1

        return None

    @property
    def term_current(self) -> Union[int, None]:
        """Current term of the permit"""
        if self.date_current_start and self.date_expiry:
            now = datetime.now().date()
            if now < self.date_expiry:
                return relativedelta(now, self.date_current_start).years +1

        return None

    @property
    def expiry_distance(self) -> Union[Tuple[int, int, int], None]:
        """Total number of terms permitted starting from initial `date_approved` ending `date_expiry`"""
        if self.date_granted and self.date_expiry:
            relative = relativedelta(self.date_expiry, datetime.now().date())
            return relative.years, relative.months, relative.days

        return None

    @property
    def date_anniversary(self) -> Union[datetime.date, None]:
        """Next anniversary date from `date_current + (current_term + 1) years`"""
        current_term = self.term_current
        if current_term:
            return self.date_current_start + relativedelta(years=self.term_current + 1)

        return None

    def __str__(self):
        return self.permit_id

    class Meta:
        unique_together = ['permit_state', 'permit_type', 'permit_number']
        ordering = ['permit_state', 'permit_type', 'permit_number']



# class Target(models.Model):
#     """These are the targets (point of interest) within a tenement,
#     these are usually stuff like hills, cliffs, patches of dirt which might be considered for operations
#     """
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='targets', unique=False)
#     name = models.CharField(max_length=100)
#     location = models.CharField(max_length=100)
#     description = models.CharField(max_length=256, blank=True, null=True)

#     def __str__(self) -> str:
#         return self.name

#     class Meta:
#         unique_together = ['project', 'name']
#         ordering = ['project']


class TenementHolder(models.Model):
    """Tenement Holders are individuals are companies that have some percentage claim of the tenement."""
    """ API Example:
    [
        {
            'Acn': '655003240',
            'Address': '7 Colo St ARANA HILLS QLD 4054',
            'Change': '',
            'Dob': None,
            'EndDate': None,
            'IsAuthorisedHolder': True,
            'MainName': 'GIGANTOR COPPER PTY LTD',
            'OtherNames': '',
            'PermitRoleTypeDescription': 'Principal Permit holder',
            'SharePercent': 100,
            'StartDate': '2022-09-26T00:00:00',
            'Status': 'Current',
            'TenancyTypeDescription': 'Sole Holder'
        }
    ],
    """
    class StatusChoices(models.TextChoices):
        CURRENT = 'C', 'Current'
        FORMER = 'F', 'Former'

    tenement = models.ForeignKey(Tenement, on_delete=models.CASCADE, related_name='holders')
    acn = models.CharField(max_length=256, null=True, blank=True)
    address = models.CharField(max_length=256)
    change = models.CharField(max_length=256)  # Not sure what this is
    status = models.CharField(max_length=256, choices=StatusChoices.choices)

    date_of_birth = models.DateField(null=True, blank=True)
    date_start = models.DateField()
    date_end = models.DateField(null=True, blank=True)

    is_authorised_holder = models.BooleanField()
    name_main = models.CharField(max_length=256)
    name_other = models.CharField(max_length=256)
    permit_role_type = models.CharField(max_length=256)
    tenancy_type_description = models.CharField(max_length=256)
    share_percent = models.FloatField(validators=[validators.MinValueValidator(1.00), validators.MaxValueValidator(100.00)])


class QLDEnvironmentalAuthority(models.Model):
    """Environmental Authority for Queensland Tenements
    See: https://apps.des.qld.gov.au/public-register/pages/ea.php?id=103163"""
    # TODO: Figure out if this can be used for other states. Though the 'qld.gov.au' implies no.
    class StatusChoices(models.TextChoices):
        CANCELLED = 0, 'Cancelled'
        EXPIRED = 1, 'Expired'
        GRANTED = 2, 'Granted'
        GRANTED_NE = 3, 'Granted - Not Effective'
        SURRENDERED = 4, 'Surrendered'
        SUSPENDED = 5, 'Suspended'

    tenement = models.OneToOneField(Tenement, on_delete=models.CASCADE, related_name='environmental_authority')
    number = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    condition_type = models.CharField(max_length=100)
    activity = models.CharField(max_length=512)
    status = models.CharField(max_length=2, choices=EnviroPermitStateChoices.choices)
    holder = models.CharField(max_length=512)
    assurance = models.FloatField(null=True, blank=True)
    date_effective = models.DateField(null=True, blank=True)


class QLDTenementBlock(models.Model):
    """Tenement Block for QLD Tenements. Where each BIM contains 1-3456 potential blocks and each block contains
    up to 25 sub-blocks represented by all alphabetical values excluding I."""
    class BIMChoices(models.TextChoices):
        # Pulled from: https://geoscience.data.qld.gov.au/data/dataset/mr000469/resource/695fad8f-d2cb-48e8-90db-8235e6f21a34
        # Need someone to verify the abbreviations
        ALIC = 'ALIC', 'Alice Springs'
        ARMI = 'ARMI', 'Armidale'
        BOUR = 'BOUR', 'Bourke'
        BRIS = 'BRIS', 'Brisbane'
        BROK = 'BROK', 'Broken Hill'
        CLON = 'CLON', 'Cloncurry'
        COOK = 'COOK', 'Cooktown'
        CLER = 'CLER', 'Clermont'
        CHAR = 'CHAR', 'Charleville'
        COOP = 'COOP', 'Cooper Creek'
        MITC = 'MITC', 'Mitchell River'
        NORM = 'NORM', 'Normanton'
        OODN = 'OODN', 'Oodnadatta'
        ROCK = 'ROCK', 'Rockhampton'
        TOWN = 'TOWN', 'Townsville'
        TORR = 'TORR', 'Torres Strait'
        NEWC = 'NEWC', 'Newcastle Waters'

    class StatusChoices(models.TextChoices):
        # Current state of the block/sub-block, C is probably not relevant and can be calculated dynamically from expiration date
        G = 'G', 'Granted'
        R = 'R', 'Relinquished'
        C = 'C', 'Current'

    # Just the default sub-blocks choices, field defaults don't like values and need functions to operate safely

    tenement = models.ForeignKey(Tenement, on_delete=models.CASCADE, related_name='blocks')
    block_identification_map = models.CharField(max_length=4, choices=BIMChoices.choices)
    number = models.IntegerField(validators=[validators.MinValueValidator(1), validators.MaxValueValidator(3456)])
    status = models.CharField(max_length=1, choices=StatusChoices.choices, default='G')

    sub_blocks = models.JSONField()

    def __str__(self):
        return f"{self.block_identification_map} {self.number}"

    @classproperty
    def default_subblocks(self):
        return dict.fromkeys('ABCDEFGHJKLMNOPQRSTUVWXYZ', False)

    class Meta:
        unique_together = ['tenement', 'block_identification_map', 'number', 'status']
        ordering = ['tenement', 'block_identification_map', 'number']


class TenementTask(models.Model):
    """A Tenement Task is a means of keeping track of compliance requirements. A user is assigned to a task and may
    upload relevant compliance documents. The due dates will be used to update the statistics box on the TMS."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenement = models.ForeignKey('Tenement', on_delete=models.CASCADE, related_name='tasks')
    authority = models.ForeignKey(User, related_name='my_tasks', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=256, blank=True, null=True)
    due_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    archived = models.BooleanField(default=False)

    files = models.ManyToManyField(MediaFile, related_name='task_file', null=True, blank=True)

    objects = TaskManager()

    @property
    def is_complete(self):
        return True if self.completion_date else False

    def as_table_row(self):
        """Used for retrieving some task information for displaying on front-end datatables"""
        task_files = self.files.all()
        return {
            'id': self.id,
            'permit': {
                'url': self.tenement.get_absolute_url(),
                'state': self.tenement.permit_state,
                'type': self.tenement.permit_type,
                'number': self.tenement.permit_number
            },
            'name': self.name,
            'description': self.description,
            'authority': self.authority.__str__(),
            'due_date': self.due_date,
            'actions': None,
            'attachments': {
                'size': MediaFile.bytes_sum_str(task_files),
                'files': [{
                    'id': file.id,
                    'url': self.tenement.project.get_file_url(file.id),
                    'filename': file.filename,
                    'size': file.file_size_str
                } for file in task_files],
            }
        }

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['due_date', '-archived']


# class TenementHolder(models.Model):
#     """A Holder is a Person of Company that 'holds' a percentage share over the tenement. This person/company may not be
#     a registered user on the website and cannot currently be stored as a foreign key.
#     """
#     tenement = models.ForeignKey('Tenement', on_delete=models.CASCADE, related_name='holders')
#     name = models.CharField(max_length=256)
#     share = models.FloatField()
#     held_from = models.DateField()
#     held_to = models.DateField(blank=True, null=True)
#     is_authorised_holder = models.BooleanField()


class Target(models.Model):
    """These are the targets (point of interest) within a tenement,
    these are usually stuff like hills, cliffs, patches of dirt which might be considered for operations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='targets', unique=False)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    description = models.CharField(max_length=256, blank=True, null=True)
    created_user = models.ForeignKey(User, on_delete=models.PROTECT)

    area = models.PointField

    # TODO: Figure out if anything else needs to go here.

    def __str__(self) -> str:
        return self.name

    class Meta:
        unique_together = ['project', 'name']
        ordering = ['project']


# # Block/Subblocks might not need to be models, we can probably generate them on the fly and pull
# # information for them from the data that selina/bishal found
# # though it's possible that the datasets pulled might be too large that an SQL query (from django) would be faster
# # so the pulled data could be added to the database when necessary
# # class Block(models.Model):
#     """A block is one of the locations within the map of australia, and a block
#     is of size 5minutes of lat/5 minutes of lon, whereas a SubBlock is 1 minute/1 minute in size
#
#     Blocks should only exist within EPM tenements as other tenements are polygonal rather than grid based.
#
#     Reverse Relationships::
#
#         block.sub_blocks : SubBlock[]
#             All block SubBlocks
#     """
#     tenement = models.ForeignKey('Tenement', on_delete=models.CASCADE, related_name='blocks')
#     block_identification_map = models.CharField(max_length=4, choices=BlockBimChoices.choices)
#     number = models.IntegerField(validators=[validators.MinValueValidator(1), validators.MaxValueValidator(3456)])
#     status = models.CharField(max_length=1, choices=BlockStateChoices.choices, default='G')
#
#     def __str__(self) -> str:
#         return f"{self.block_identification_map} {self.number}"
#
#     def get_sub_block_list(self):
#         """ Gets all the sub-blocks by alphabetical letter for easy tables in jinja2
#         e.g, [None, B, None, None, E, ... , None, Y, Z]
#         """
#         items = {letter: None for letter in "ABCDEFGHJKLMNOPQRSTUVWXYZ"}
#
#         for sub_block in self.sub_blocks.all():
#             items[sub_block.number] = sub_block
#
#         return items.values()
#
#     class Meta:
#         unique_together = ['tenement', 'block_identification_map', 'number']
#
#
# class SubBlock(models.Model):
#     """A Sub-Block is contained within a Block where a block is divided into 25 individual sub-blocks
#     where a subblock number is A-Z excluding I
#     """
#     block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='sub_blocks')
#     number = models.CharField(max_length=2, choices=SUBBLOCK_CHOICES)
#     status = models.CharField(max_length=1, choices=BlockStateChoices.choices, default='G')
#
#     def __str__(self) -> str:
#         return f"{self.block.__str__()} {self.number}"
#
#     class Meta:
#         # Custom validator required as a sub-block could have history with other tenements, we cannot
#         # access the blocks fields (tenement) for proper unique constraints.
#         # Alternatively, we can override the models clean() function
#         unique_together = ['block', 'number']


class WorkProgram(models.Model):
    """Work Program object for a specific Tenement. Each discpline has a number of activities available to it.

    Notable Methods :

        WorkProgram.ActivityChoices.choices_by_discipline(discipline) : []
            Returns a list of activities for supplies discipline, although the same can be done by using
            individual functions e.g., `Activity.desktop_studies_choices()`

        WorkProgram.ActivityChoices.choices_json() : []
            Returns a nested list of choices, numerical index matches discipline value
    """
    class Discipline:
        """Work Program Disciplines

        Each member variable is a tuple of ID, Name, Units and Quantity.
        """
        DESKTOP_STUDIES = 0, 'Desktop Studies', 'Days', 'N/A'
        DRILLING = 1, 'Drilling', 'Holes', 'Metres'
        FEASIBILITY_STUDIES = 2, 'Feasibility Studies', 'Days', 'N/A'
        GEOPHYSICS = 3, 'Geophysics', 'Lines', 'Line Kilometres'
        MAPPING = 4, 'Mapping', 'Days', 'N/A'
        REMOTE_SENSING = 5, 'Remote Sensing', 'Lines', 'Line Kilometres'
        RESOURCE_EVALUATION = 6, 'Resource Evaluation', 'Days', 'N/A'
        SAMPLE_ANALYSIS = 7, 'Sample Analysis', 'Samples', 'N/A'
        SAMPLE_COLLECTION = 8, 'Sample Collection', 'Samples', 'Kilograms'
        SITE_LOGISTICS = 9, 'Site Logistics', 'Days', 'N/A'
        SITE_TECHNICAL = 10, 'Site Technical', 'Days', 'N/A'

        @classmethod
        def __iter__(cls):
            """Iterates over the class member choices, as a list of tuples with length 4"""
            return iter(v for k, v in cls.__dict__.items() if not callable(getattr(cls, k)) and not k.startswith('__'))

        @classmethod
        def choices(cls) -> List[Tuple[int, str]]:
            """Returns the ID and Discipline label choices"""
            return [(i, d) for i, d, _, _ in cls.__iter__()]

        @classmethod
        def units_choices(cls) -> List[Tuple[int, str]]:
            """Returns the ID and Unit label choices"""
            return [(i, u) for i, _, u, _ in cls.__iter__()]

        @classmethod
        def quantity_choices(cls) -> List[Tuple[int, str]]:
            """Returns the ID and Quantity label choices"""
            return [(i, q) for i, _, _, q in cls.__iter__()]

    class Activity(models.IntegerChoices):
        """Possible Activites within a WorkProgram, these exist as sub-categories under each discipline.

        See :

            Activity.choices_by_discipline(discipline) : []
                Returns a list of activities for supplies discipline, although the same can be done by using
                individual functions e.g., `Activity.desktop_studies_choices()`

            Activity.choices_json() : []
                Returns a nested list of choices, numerical index matches discipline value
        """
        # DESKTOP_STUDIES
        CONSULTANCY_STUDIES = 0, 'Consultancy Studies'
        GEOLOGICAL_AND_GEOPHYSICAL_REVIEW = 1, 'Geological and Geophysical Review'
        GEOPHYSICAL_DATA_REPROCESSING = 2, 'Geophysical Data Reprocessing'
        GRAVITY_DATA_REPROCESSING = 3, 'Gravity Data Reprocessing'
        GRAVITY_DATA_REPROCESSING_FIXED_COST = 4, 'Gravity Data Reprocessing (Fixed Cost)'
        MAGNETIC_DATA_REPROCESSING = 5, 'Magnetic Data Reprocessing'
        MAGNETIC_DATA_REPROCESSING_FIXED_COST = 6, 'Magnetic Data Reprocessing (Fixed Cost)'
        SEISMIC_DATA_REPROCESSING = 7, 'Seismic Data Reprocessing'
        SEISMIC_DATA_REPROCESSING_FIXED_COST = 8, 'Seismic Data Reprocessing (Fixed Cost)'
        TECHNICAL_REVIEW = 9, 'Technical Review'

        @classmethod
        def desktop_studies_choices(cls) -> List[Tuple[int, str]]:
            return cls.choices[0:10]

        # DRILLING
        AIR_CORE_DRILLING = 10, 'Air Core Drilling'
        AUGUR_DRILLING = 11, 'Augur Drilling'
        DIAMOND = 12, 'Diamond'
        DIRECTIONAL = 13, 'Directional'
        GEOTECHNICAL_DRILLING = 14, 'Geotechnical Drilling'
        HAMMER = 15, 'Hammer'
        LARGE_DIAMETER = 16, 'Large Diameter'
        MIXED_TYPE = 17, 'Mixed Type'
        MUD = 18, 'Mud'
        PERCUSSION = 19, 'Percussion'
        PRECOLLAR = 20, 'Precollar'
        REVERSE_CIRCULATION = 21, 'Reverse Circulation'
        SONIC_VIBRATORY_DRILLING = 22, 'Sonic/Vibratory Drilling'
        TRI_CONE = 23, 'Tri-Cone'

        @classmethod
        def drilling_choices(cls) -> List[Tuple[int, str]]:
            return cls.choices[10:24]

        # FEASIBILITY_STUDIES
        BANKABLE_FEASIBILITY_STUDY_BFS = 24, 'Bankable Feasibility Study (BFS)'
        DEFINITIVE_FEASIBILITY_STUDY_DFS = 25, 'Definitive Feasibility Study (DFS)'
        ENGINEERING_AND_DESIGN = 26, 'Engineering and Design'
        ENVIRONMENTAL_ASSESSMENT = 27, 'Environmental Assessment'
        MARKET_ANALYSIS = 28, 'Market Analysis'
        MINE_PLANNING = 29, 'Mine Planning'
        PRELIMINARY_FEASIBILITY_STUDY_PFS = 30, 'Preliminary Feasibility Study (PFS)'
        SCOPING_STUDY = 31, 'Scoping Study'

        @classmethod
        def feasibility_studies_choices(cls) -> List[Tuple[int, str]]:
            return cls.choices[24:32]

        # GEOPHYSICS
        DOWNHOLE_GEOPHYSICS = 32, 'Downhole Geophysics'
        DOWNHOLE_SURVEY = 33, 'Downhole Survey'
        ELECTROMAGNETIC = 34, 'Electromagnetic'
        GRAVITY = 35, 'Gravity'
        GROUND_PENETRATING_RADAR = 36, 'Ground Penetrating Radar'
        INDUCE_POLARISATION = 37, 'Induce Polarisation'
        MAGNETICS = 38, 'Magnetics'
        MAGNETOTELLURICS = 39, 'Magnetotellurics'
        RADIOMETRIC = 40, 'Radiometric'
        RESISTIVITY = 41, 'Resistivity'
        SEISMIC_2_DIMENSIONAL = 42, 'Seismic (2 Dimensional)'
        SEISMIC_3_DIMENSIONAL = 43, 'Seismic (3 Dimensional)'
        SELF_POTENTIAL = 44, 'Self Potential'
        SUB_AUDIO_MAGNETICS = 45, 'Sub-audio Magnetics'

        @classmethod
        def geophysics_choices(cls) -> List[Tuple[int, str]]:
            return cls.choices[32:46]

        # MAPPING
        ALTERATION = 46, 'Alteration'
        GEOLOGICAL = 47, 'Geological'
        RECONNAISSANCE = 48, 'Reconnaissance'
        STRUCTURAL = 49, 'Structural'

        @classmethod
        def mapping_choices(cls) -> List[Tuple[int, str]]:
            return cls.choices[46:50]

        # REMOTE_SENSING
        AERIAL_PHOTOGRAPHY_BROADER_SPECTRUM_IMAGERY = 50, 'Aerial Photography (Broader Spectrum Imagery)'
        INTERPRETATION_AND_MODELLING = 51, 'Interpretation and Modelling'
        AERIAL_PHOTOGRAPHY_VISIBLE_IMAGERY = 52, 'Aerial Photography (Visible Imagery)'
        BROADER_SPECTRUM_IMAGERY = 53, 'Broader Spectrum Imagery'
        SATELLITE_IMAGERY_VISIBLE_IMAGERY = 54, 'Satellite Imagery (Visible Imagery)'

        @classmethod
        def remote_sensing_choices(cls) -> List[Tuple[int, str]]:
            return cls.choices[50:55]

        # RESOURCE_EVALUATION
        METALLURGICAL_STUDIES = 55, 'Metallurgical Studies'
        GEOLOGICAL_MODELLING = 56, 'Geological Modelling'
        JORC_RESOURCE_ESTIMATION = 57, 'JORC Resource Estimation'
        RESOURCE_MODELLING = 58, 'Resource Modelling'

        @classmethod
        def resource_evaluation_choices(cls) -> List[Tuple[int, str]]:
            return cls.choices[55:59]

        # SAMPLE_ANALYSIS
        BULK_LEACH_EXTRACTED_GOLD = 59, 'Bulk Leach Extracted Gold'
        CHROMATOGRAPHIC_SOILS_GAS = 60, 'Chromatographic Soils/Gas'
        DRILL_SAMPLE_ASSAYS = 61, 'Drill Sample Assays'
        GENERAL_SAMPLE_ASSAYS = 62, 'General Sample Assays'
        MINERAL_PETROLOGY = 63, 'Mineral/Petrology'
        MOBILE_METAL_ION = 64, 'Mobile Metal Ion'
        MULTI_ELEMENT = 65, 'Multi-Element'
        PORTABLE_ANALYTICAL_TOOLS = 66, 'Portable Analytical Tools'
        ANALYSIS_ROCK_CHIPS = 67, 'Rock Chips'
        ANALYSIS_SOILS = 68, 'Soils'

        @classmethod
        def sample_analysis_choices(cls) -> List[Tuple[int, str]]:
            return cls.choices[59:69]

        # SAMPLE_COLLECTION
        COSTEANING = 69, 'Costeaning'
        HAND_SAMPLING = 70, 'Hand Sampling'
        COLLECTION_ROCK_CHIPS = 71, 'Rock Chips'
        COLLECTION_SOILS = 72, 'Soils'
        STREAM_SEDIMENTS = 73, 'Stream Sediments'
        TRENCHING = 74, 'Trenching'

        @classmethod
        def sample_collection_choices(cls) -> List[Tuple[int, str]]:
            return cls.choices[69:75]

        # SITE_LOGISTICS
        ACCESS_OR_DRILL_SITE_PREPARATION_COSTS = 75, 'Access or Drill Site Preparation costs'
        VEHICLE_ACCOMODATION = 76, 'Vehicle / Accomodation'
        REHABILITIATION_COSTS = 77, 'Rehabilitiation costs'

        @classmethod
        def site_logistics_choices(cls) -> List[Tuple[int, str]]:
            return cls.choices[75:78]

        # SITE_TECHNICAL
        CHIP_LOGGING = 78, 'Chip logging'
        CONSULTANCY_COST = 79, 'Consultancy Cost'
        CORE_LOGGING = 80, 'Core logging'
        GEOTECHNICAL_LOGGING = 81, 'Geotechnical logging'
        INTERNAL_PROJECT_STAFF_COST = 82, 'Internal Project Staff Cost'
        PROGRAM_SUPERVISION = 83, 'Program Supervision'

        @classmethod
        def site_technical_choices(cls) -> List[Tuple[int, str]]:
            return cls.choices[78:84]

        @classmethod
        def choices_by_discipline(cls, discipline: Union[int, str]) -> List[Tuple[int, str]]:
            """Returns choices available per discipline. Can be called using Discipline name or integer index."""
            # Allow for indexing either by ID or string name
            if isinstance(discipline, int):
                option = 0
            elif isinstance(discipline, str):
                option = 1
            else:
                raise TypeError("Discipline must be either a string or integer")

            if discipline == WorkProgram.Discipline.DESKTOP_STUDIES[option]:
                return cls.desktop_studies_choices()

            elif discipline == WorkProgram.Discipline.DRILLING[option]:
                return cls.drilling_choices()

            elif discipline == WorkProgram.Discipline.FEASIBILITY_STUDIES[option]:
                return cls.feasibility_studies_choices()

            elif discipline == WorkProgram.Discipline.GEOPHYSICS[option]:
                return cls.geophysics_choices()

            elif discipline == WorkProgram.Discipline.MAPPING[option]:
                return cls.mapping_choices()

            elif discipline == WorkProgram.Discipline.REMOTE_SENSING[option]:
                return cls.remote_sensing_choices()

            elif discipline == WorkProgram.Discipline.RESOURCE_EVALUATION[option]:
                return cls.resource_evaluation_choices()

            elif discipline == WorkProgram.Discipline.SAMPLE_ANALYSIS[option]:
                return cls.sample_analysis_choices()

            elif discipline == WorkProgram.Discipline.SAMPLE_COLLECTION[option]:
                return cls.sample_collection_choices()

            elif discipline == WorkProgram.Discipline.SITE_LOGISTICS[option]:
                return cls.site_logistics_choices()

            elif discipline == WorkProgram.Discipline.SITE_TECHNICAL[option]:
                return cls.site_technical_choices()
            else:
                raise IndexError(f"Invalid Index at position {discipline}")

        @classmethod
        def choices_json(cls) -> List[List[Tuple[int, str]]]:
            return [cls.choices_by_discipline(i) for i, v in WorkProgram.Discipline.choices()]

    # WorkProgram Model Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenement = models.ForeignKey('Tenement', on_delete=models.CASCADE, related_name='work_programs', unique=False)
    estimated_expenditure = models.FloatField()

    year = models.PositiveIntegerField()
    discipline = models.IntegerField(choices=Discipline.choices())
    activity = models.IntegerField(choices=Activity.choices)

    units = models.FloatField()
    quantity = models.FloatField(default=0.0)

    slug = models.SlugField(max_length=200)

    # COST TRACKER STUFF
    @property
    def actual_expenditure(self):
        """Returns the actual expenditure of this work program. Aggregates the sum of all receipt costs."""
        return self.receipts.all().only('cost').aggregate(total_expense=Sum('cost'))['total_expense']

    @staticmethod
    def aggregate_yearly_disciplines(queryset: QuerySet["WorkProgram"]) -> QuerySet["WorkProgram"]:
        """Returns an aggregation of all year/discipline combinations.

        Examples :

            >>> WorkProgram.aggregate_yearly_disciplines(tenement.work_program.all())
            [
                {
                    'year': 1,
                    'discipline': 0,
                    'discipline_display': "Desktop Studies",
                    'estimated_expenditure', "Consultancy Studies",
                    'units': 10,
                    'units_label': "Days",
                    'quantity':, 5,
                    'quantity_label': "N/A",
                },
                {
                    ...
                }
            ]

        # TODO: Decide whether this belongs under the WorkProgram class or the Tenement Class
        """
        return queryset.values('year', 'discipline').annotate(
            discipline_display=ChoicesLabelCase('discipline', WorkProgram.Discipline.choices()),
            estimated_expenditure=Sum('estimated_expenditure'),
            actual_expenditure=Sum('receipts__cost'),
            units=Sum('units'),
            units_display=ChoicesLabelCase('discipline', WorkProgram.Discipline.units_choices()),
            quantity=Sum('quantity'),
            quantity_display=ChoicesLabelCase('discipline', WorkProgram.Discipline.quantity_choices())
        )

    @staticmethod
    def get_yearly_totals(queryset: QuerySet["WorkProgram"]) -> QuerySet["WorkProgram"]:
        """Returns the yearly totals as a QueryDict
        TODO: This can probably just be performed on the frontend to save time
        """
        return queryset.values('year').annotate(
            estimated_expenditure=Sum('estimated_expenditure'),
            actual_expenditure=Sum('receipts__cost'),
        )

    def file_directory(self):
        """Where the work program receipts will be uploaded"""
        return f'{self.tenement.file_directory()}/work_program/{self.slug}'

    def save(self, *args, **kwargs):
        """Override the save method to auto-generate a slug"""
        if not self.pk:
            self.slug = slugify(f"Y{self.year}_{self.get_discipline_display()}_{self.get_activity_display()}")

        super().save(*args, **kwargs)


    def __str__(self):
        return f'Year {self.year}, {self.get_discipline_display()}, {self.get_activity_display()}'

    class Meta:
        unique_together = ['tenement', 'year', 'discipline', 'activity']
        ordering = ['tenement', 'year', 'discipline', 'activity']


class WorkProgramReceipt(models.Model):
    """A Receipt for a work program activity. Where each activity may have multiple expenses throughout the year."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_program = models.ForeignKey(WorkProgram, related_name='receipts', on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=32)
    description = models.CharField(max_length=256, null=True, blank=True)

    cost = models.FloatField()
    date_created = models.DateField(auto_now_add=True)

    # One receipt per expense, though as this is a foreign key we need to handle the deletion of files
    # via a signal since the 'on_delete' is handled one way only.
    file = models.ForeignKey(MediaFile, related_name='receipt_files', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

#
# PERMIT_CHOICES = {
#     AustraliaStateChoices.QLD.name: {
#         'state': AustraliaStateChoices.QLD.value,
#         'permit_types': [
#             ('EPM', 'Exploration Permit for Minerals'),
#             ('MDL', 'Mineral Development Lease'),
#             ('ML', 'Mining Lease'),
#             ('EPC', 'Exploration Permit for Coal'),
#             ('ATP', 'Authorities to Prospect for Petroleum')
#         ],
#         'permit_status': [
#             ('G', 'Granted'),
#             ('C', 'Current'),
#             ('A', 'Application'),
#             ('AP', 'Application (Priority Applicant)'),
#             ('AR', 'Application (Ranked)'),
#             ('RA', 'Renewal Application Lodged'),
#             ('W', 'Withdrawn'),
#             ('Z', 'Achieved',),
#             ('T', 'Temporary'),
#             ('S', 'Surrendered'),
#             ('N', 'Non-Current')
#         ],
#         'enviro_status': [
#             ('G', 'Granted'),
#             ('GN', 'Granted - Not Effective'),
#             ('X', 'Suspended'),
#             ('S', 'Surrendered'),
#             ('C', 'Cancelled'),
#             ('E', 'Expired'),
#         ]
#     },
#     AustraliaStateChoices.WA.name: {
#         'permit_types': [
#             ('ASD', 'ASD'),
#             ('QWE', 'QWE'),
#             ('ZXC', 'ZXC'),
#         ],
#         'permit_status': [
#             ('G', 'Granted'),
#             ('C', 'Current'),
#             ('A', 'Application'),
#             ('AP', 'Application (Priority Applicant)'),
#             ('AR', 'Application (Ranked)'),
#             ('RA', 'Renewal Application Lodged'),
#             ('W', 'Withdrawn'),
#             ('Z', 'Achieved',),
#             ('T', 'Temporary'),
#             ('S', 'Surrendered'),
#             ('N', 'Non-Current')
#         ],
#         'enviro_status': [
#             ('G', 'Granted'),
#             ('GN', 'Granted - Not Effective'),
#             ('X', 'Suspended'),
#             ('S', 'Surrendered'),
#             ('C', 'Cancelled'),
#             ('E', 'Expired'),
#         ]
#     }
# }
