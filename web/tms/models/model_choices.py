from django.utils.translation import gettext_lazy as _
from django.db import models


class AustraliaStateChoices(models.TextChoices):
    QLD = 'QLD', 'Queensland'
    NSW = 'NSW', 'New South Wales'
    VIC = 'VIC', 'Victoria'
    SA = 'SA', 'South Australia'
    WA = 'WA', 'Western Australia'
    NT = 'NT', 'Northern Territory'
    TAS = 'TAS', 'Tasmania'
    ACT = 'ACT', 'Australian Capital Territory'


class PermitTypeChoices:
    CHOICES = {
        AustraliaStateChoices.QLD: [
            ('EPM', 'Exploration Permit for Minerals'),
            ('MDL', 'Mining Development Licence'),
            ('ML', 'Mining Lease'),
            ('EPC', 'Exploration Permit for Coal'),
            ('ATP', 'Authorities to Prospect for Petroleum'),
        ],
        AustraliaStateChoices.WA: [
            ('CML', 'Coal Mining Lease'),
            ('MEL', 'Commonwealth Exploration'),
            ('E', 'Exploration License'),
            ('EOS', 'Exploration License Offshore'),
            ('G', 'General Purpose Lease'),
            ('AG', 'General Purpose Lease S.A.'),
            ('LTT', 'License to Treat Tailings'),
            ('MC', 'Mineral Claim'),
            ('ML', 'Mineral Lease'),
            ('AML', 'Mineral Lease S.A.'),
            ('M', 'Mining Lease'),
            ('AM', 'Mining Lease S.A.'),
            ('L', 'Miscellaneous Licence'),
            ('AL', 'Miscellaneous Licence S.A.'),
            ('P', 'Prospecting Licence'),
            ('R', 'Retention Licence'),
            ('TR', 'Temporary Reserver'),
        ],
        AustraliaStateChoices.VIC: [
            ('DL', 'Development Lease'),
            ('EL', 'Exploration License'),
            ('LSE', 'Extractive Industry Lease'),
            ('LIC', 'Extractive Industry Licence'),
            ('ESP', 'Extractive Search Permit'),
            ('GML', 'Gold Mining Lease'),
            ('MIL', 'Mineral Lease'),
            ('SL', 'Mineral Search Licence'),
            ('MRC', "Miner's Right Claim"),
            ('ML', 'Mining Lease'),
            ('MLA', 'Mining Lease Application'),
            ('MAL', 'Mining Area Licence'),
            ('MN', 'Mining Licence'),
            ('SPC', 'Not Operating Under Our Acts'),
            ('PL', 'Prospecting Licence'),
            ('PAL', 'Prospecting Area Licence'),
            ('RL', 'Retention Licence'),
            ('SML', 'Special Mining Lease'),
            ('TL', 'Tailings Licence'),
            ('TRL', 'Tailings Removal Licence'),
            ('TTL', 'Tailings Treatment Licence'),
            ('TMA', 'Tourist Mining Authority'),
            ('WLL', 'Water Line Licence'),
            ('WA', 'Work Authority'),
        ]
    }

    @classmethod
    def choices(cls, include_state=False):
        return [
            (state, abbr, display) if include_state else (abbr, display)
            for state, choices in cls.CHOICES.items()
            for abbr, display in choices
        ]

    @classmethod
    def get_state(cls, state, ):
        return cls.CHOICES[state]

    @classmethod
    def get_display(cls, state, permit_abbr):
        """Returns display label for a particular state/permit type pair"""
        for abbr, permit_type in cls.CHOICES[state]:
            if abbr == permit_abbr:
                return permit_type

        raise IndexError()


class PermitStatusChoices(models.TextChoices):
    # TODO: Confirm whether this are correct or items are missing
    G = 'G', _('Granted')
    C = 'C', _('Current')
    A = 'A', _('Application')
    AP = 'AP', _('Application (Priority Applicant)')
    AR = 'AR', _('Application (Ranked)')
    RA = 'RA', _('Renewal Application Lodged')
    W = 'W', _('Withdrawn')
    Z = 'Z', _('Achieved')
    T = 'T', _('Temporary')
    S = 'S', _('Surrendered')
    N = 'N', _('Non-current')


class EnviroPermitStateChoices(models.TextChoices):
    # Taken from the downloaded copy of all current EA's
    G = 'G', _('Granted')
    GN = 'GN', _('Granted - Not Effective')
    X = 'X', _('Suspended')
    S = 'S', _('Surrendered')
    C = 'C', _('Cancelled')
    E = 'E', _('Expired')


class BlockBimChoices(models.TextChoices):
    # Pulled from: https://geoscience.data.qld.gov.au/data/dataset/mr000469/resource/695fad8f-d2cb-48e8-90db-8235e6f21a34
    # Need someone to verify the abbreviations
    ALIC = 'ALIC', _('Alice Springs')
    ARMI = 'ARMI', _('Armidale')
    BOUR = 'BOUR', _('Bourke')
    BRIS = 'BRIS', _('Brisbane')
    BROK = 'BROK', _('Broken Hill')
    CLON = 'CLON', _('Cloncurry')
    COOK = 'COOK', _('Cooktown')
    CLER = 'CLER', _('Clermont')
    CHAR = 'CHAR', _('Charleville')
    COOP = 'COOP', _('Cooper Creek')
    MITC = 'MITC', _('Mitchell River')
    NORM = 'NORM', _('Normanton')
    OODN = 'OODN', _('Oodnadatta')
    ROCK = 'ROCK', _('Rockhampton')
    TOWN = 'TOWN', _('Townsville')
    TORR = 'TORR', _('Torres Strait')
    NEWC = 'NEWC', _('Newcastle Waters')


class BlockStateChoices(models.TextChoices):
    # Current state of the block/sub-block, C is probably not relevant and can be calculated dynamically from expiration date
    G = 'G', _('Granted')  # Blocks/Sub-blocks included when the tenement was granted
    R = 'R', _('Relinquished')  # Blocks/Sub-blocks that have been relinquished
    C = 'C', _('Current')  # Current Blocks/Sub-blocks of the Tenement
