import json
import uuid
from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.contrib.gis.geos import MultiPolygon
from django.contrib.gis.db.models.functions import Area
from django.core import serializers
from django.core.exceptions import ValidationError
from django.db.models import UniqueConstraint, CheckConstraint, Q, Sum
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.postgres import fields

from lms.managers import LandParcelManager, ParcelProjectManager
from media_file.models import MediaFile
from native_title_management.managers import NativeTitleManager
from project.models import Project
from tms.models import AustraliaStateChoices

User = get_user_model()


METHOD_CHOICES = [
        (0, 'Consent'),
        (1, 'Litigated'),
        (2, 'Unopposed'),
]
STATUS_CHOICES = [
    (0, 'In effect - Finalised'),
    (1, 'In effect - Not Finalised'),
    (2, 'Conditional - Full'),
    (3, 'Conditional - Part'),
]
OUTCOME_CHOICES = [
    (0, 'Native title does not exist'),
    (1, 'Native title exists (exclusive)'),
    (2, 'Native title exists (non-exclusive)'),
    (3, 'Native title extinguished'),
    (4, 'Native title exists in parts of the determination area'),
    (5, 'Native title exists in the entire determination area'),
    (6, 'Compensation is payable'),
]
CLAIMANT_CHOICES = [
    (0, 'Claimant'),
    (1, 'Non-Claimant'),
    (2, 'Compensation'),
    (3, 'Revised Determination'),
]
APPLICATION_STATUS_CHOICES = [
    (0, 'Active'),
]
REG_TEST_STATUS_CHOICES = [
    (0, 'Accepted for registration'),
    (1, 'Accepted for registration (new decision in progress - s 190A)'),
    (2, 'Currently identified for Reg. Decision (new decision in progress - s 190A)'),
    (3, 'Currently identified for Reg. Decision (new decision in progress - s 190E reconsideration)'),
    (4, 'Not Accepted for registration'),
    (5, 'Not currently identified for Reg. Decision'),
    (6, 'Not currently identified for Reg. Decision (new decision in progress - s 190A)'),
]

# https://services2.arcgis.com/rzk7fNEt0xoEp3cX/ArcGIS/rest/services/NNTT_Custodial_AGOL/FeatureServer

class NativeTitleApplication(models.Model):
    # Native Title Applications, Registration Decisions and Determinations
    # Example: http://www.nntt.gov.au/searchRegApps/NativeTitleClaims/Pages/details.aspx?NTDA_Fileno=DC2001/021

    tribunal_number = models.CharField(max_length=64, unique=True)  # ID number on the NNTT register
    name = models.CharField(max_length=256)  # Application Name
    federal_court_number = models.CharField(max_length=64, unique=True)  # Case number

    date_lodged = models.DateField()
    status = models.PositiveSmallIntegerField(choices=[
        (0, ''),
        (1, ''),
        (2, ''),
        (3, ''),
    ])
    date_status = models.DateField()
    registered_status = models.CharField(max_length=64)  # Some string representation of the resitration
    date_registered = models.DateField()
    date_registered_decision = models.DateField()
    date_entri = models.DateField()
    date_notncl = models.DateField(null=True, blank=True)
    date_fcord = models.DateField(null=True, blank=True)

    combined = models.BooleanField(choices=[(False, 'N'), (True, 'Y')], default=False, null=True, blank=True)
    parent_no = models.CharField(max_length=64, null=True, blank=True)  # No Idea

    representative = models.CharField(max_length=64, null=True, blank=True)  # Lawyer or firm?

    application_type = models.PositiveSmallIntegerField(choices=[
        (0, 'Claimant'),
        (1, 'Non-Claimant'),
        (2, 'Compensation'),
        (3, 'Revised Determination'),
    ], null=True, blank=True)  # This field is not used in the 'outcomes' dataset.

    data_source = models.CharField(max_length=64)  # Might have something to do with RATSIB Areas

    date_curr = models.DateField()

    sea_claim = models.BooleanField(choices=[(False, 'N'), (True, 'Y')], default=False)
    zone_lwm = models.BooleanField(choices=[(False, 'N'), (True, 'Y')], default=False)
    zone_3nm = models.BooleanField(choices=[(False, 'N'), (True, 'Y')], default=False)  # Something nautical miles?
    zone_12nm = models.BooleanField(choices=[(False, 'N'), (True, 'Y')], default=False)
    zone_24nm = models.BooleanField(choices=[(False, 'N'), (True, 'Y')], default=False)
    zone_eez = models.BooleanField(choices=[(False, 'N'), (True, 'Y')], default=False)

    NNTT_seq_no = models.CharField(max_length=64, unique=True)  # This links to a pdf on the nntt.gov.au, but the data only contains pdf name
    sptial_note = models.CharField(max_length=64, unique=True)  # This links to a pdf on the nntt.gov.au, but the data only contains pdf name

    jurisdiction = models.CharField(max_length=3, choices=AustraliaStateChoices.choices)
    overlap = models.CharField(max_length=64, null=True, blank=True)  # Not sure what this is, its NULL for all rows

    date_extracted = models.DateField()  # No idea what this is for


class NativeTitleDetermination(models.Model):
    """This model shares fields with NativeTitleDetermination and NativeTitleDeterminationOutcome"""
    # National Native Title Register Details
    # Example: http://www.nntt.gov.au/searchRegApps/NativeTitleRegisters/Pages/NNTR_details.aspx?NNTT_Fileno=SCD2014/001

    tribunal_number = models.CharField(max_length=64, unique=True)  # ID number on the NNTT register
    name = models.CharField(max_length=256)  # Not entirely sure
    federal_court_number = fields.ArrayField(models.CharField(max_length=100), default=list)  # Case number
    federal_court_name = models.CharField(max_length=512, null=True, blank=True)  # Case name
    linked_file_no = models.CharField(max_length=1024, null=True, blank=True)  # Case link

    date_determined = models.DateField(null=True, blank=True)
    date_registered = models.DateField(null=True, blank=True)

    method = models.PositiveSmallIntegerField(choices=METHOD_CHOICES)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES)
    outcome = models.PositiveSmallIntegerField(choices=OUTCOME_CHOICES)
    claimant_type = models.PositiveSmallIntegerField(choices=CLAIMANT_CHOICES, null=True, blank=True)  # This field is not used in the 'outcomes' dataset.

    RNTBC_name = models.CharField(max_length=512, null=True, blank=True)  # Registered Native Title Bodies Corporate
    related_NTDA = fields.ArrayField(models.CharField(max_length=100), default=list)  # NT Application/Registration decision/Determination (multiple)
    date_currency = models.DateField(null=True, blank=True)
    NNTT_seq_no = models.CharField(max_length=64, null=True, blank=True)  # This links to a pdf on the nntt.gov.au, but the data only contains pdf name

    jurisdiction = models.CharField(max_length=3, choices=AustraliaStateChoices.choices)
    overlap = models.CharField(max_length=64, null=True, blank=True)  # Not sure what this is, its NULL for all rows

    # Might be interested in the following:
    # - Representative A/TSI body area(s)
    # - Local government area(s)

    date_extracted = models.DateField(null=True, blank=True)  # No idea what this is for

    geometry = models.GeometryField()

    objects = NativeTitleManager()


class NativeTitleClaimApplication(models.Model):

    tribunal_number = models.CharField(max_length=64, unique=True)  # ID number on the NNTT register
    name = models.CharField(max_length=256)  # Not entirely sure
    federal_court_number = models.CharField(max_length=100)  # Case number
    date_lodged = models.DateField(null=True, blank=True)  # lodged
    status = models.PositiveSmallIntegerField(choices=APPLICATION_STATUS_CHOICES)
    sub_status = models.PositiveSmallIntegerField(choices=REG_TEST_STATUS_CHOICES)  # reg_test_status
    date_status_effective = models.DateField(null=True, blank=True)  # date_lodged default
    representative = models.CharField(max_length=512, null=True, blank=True)

    date_registered = models.DateField(null=True, blank=True, verbose_name="Date current reg")  # date_registered

    # NNTT_seq_no = models.CharField(max_length=64, null=True, blank=True)

    jurisdiction = models.CharField(max_length=3, choices=AustraliaStateChoices.choices)
    overlap = models.CharField(max_length=3, choices=AustraliaStateChoices.choices, null=True, blank=True)

    geometry = models.GeometryField()

    objects = NativeTitleManager()

    def __str__(self):
        return f"{self.tribunal_number} {self.name}"


class LandSubjectToNativeTitleIndicationOnly(models.Model):
    pass
