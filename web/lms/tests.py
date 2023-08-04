from pyexpat import model
import uuid
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from lms.models import Parcel



def M(geom):
    if isinstance(geom, Polygon):
        geom = MultiPolygon([geom])
    return geom

dummy_parcels = [
    Parcel(id=uuid.UUID(int=1), feature_name="a", lot=73, plan="GEORGE", tenure="Beetles", geometry=M(
            GEOSGeometry(
                '{"type": "Polygon", "coordinates": [ [ [ 152.802046115000053, -27.371197363999954 ], '
                '[ 152.802128377000031, -27.371642565999935 ], [ 152.80042878800009, -27.372242642999936 ], '
                '[ 152.800253558000122, -27.372314421999931 ], [ 152.800342026000067, -27.371760157999972 ], '
                '[ 152.800975660000063, -27.371536491999962 ], [ 152.801704268000094, -27.371277628999962 ], '
                '[ 152.802046115000053, -27.371197363999954 ] ] ]}'
            )
        )
    ),
    Parcel(id=uuid.UUID(int=2), feature_name="b", lot=42, plan="POTATO", tenure="Starch Free", geometry=M(
            GEOSGeometry(
                '{"type": "Polygon", "coordinates": [ [ [ 152.802013161000104, -27.371019309999951 ], '
                '[ 152.802046115000053, -27.371197363999954 ], [ 152.801704268000094, -27.371277628999962 ], '
                '[ 152.800975660000063, -27.371536491999962 ], [ 152.800342026000067, -27.371760157999972 ], '
                '[ 152.800253558000122, -27.372314421999931 ], [ 152.798966366000059, -27.372841602999983 ], '
                '[ 152.798769082000035, -27.372881492999966 ], [ 152.79705668500003, -27.373228138999934 ], '
                '[ 152.79583883500004, -27.373530005999953 ], [ 152.794812026000045, -27.37356280399996 ], '
                '[ 152.794229249000068, -27.373905388999958 ], [ 152.79326095700003, -27.374304180999957 ], '
                '[ 152.791985596000018, -27.373340902999928 ], [ 152.791864025000109, -27.373023448999959 ], '
                '[ 152.792053970000097, -27.371783619999974 ], [ 152.791469852000091, -27.370661964999954 ], '
                '[ 152.791429865000055, -27.370111031999954 ], [ 152.791554178000069, -27.369184126999983 ], '
                '[ 152.791907648000119, -27.367133883999941 ], [ 152.793128277000051, -27.36731894199994 ], '
                '[ 152.793407875000071, -27.367354100999933 ], [ 152.793245802000115, -27.371205000999964 ], '
                '[ 152.797433297000111, -27.371466500999929 ], [ 152.80046453600005, -27.371658882999952 ], '
                '[ 152.800956319000079, -27.371485194999934 ], [ 152.802013161000104, -27.371019309999951 ] ] ]}'
            )
        )
    ),
]

class LMSModelTestCase(TestCase):

    def setUp(self) -> None:
        Parcel.objects.bulk_create(dummy_parcels)

class ParcelTestCase(LMSModelTestCase):
    
    def setUp(self) -> None:
        self.current_parcel = Parcel.objects.create(
            lot="1234",
            plan="ABCDEF",
            tenure="Freehold",
            shire_name="Test Shire",
            feature_name="Test Feature",
            alias_name="Test Alias",
            locality="Test Locality",
            parcel_type="Test Parcel Type",
            cover_type="Test Cover",
            accuracy_code="Test Accuracy Code",
            smis_map="Test SMIS Map",
            geometry="POINT(0 0)"
        )

        return super().setUp()
    
    def test_str(self):
        self.assertEqual(str(self.current_parcel), "1234ABCDEF")

    def test_lot_plan__return_correct_lotplan(self) -> None:
        """
        Input: 
        - parcel

        Assertion: 
        - property lot_plan is a string of "<lot><plan>"
        """
        for parcel in Parcel.objects.all():
            self.assertEqual(parcel.lot_plan, parcel.lot + parcel.plan )

    def test_lot_is_nullable(self):
        """
        Add parcel without lot will have empty lot
        """
        parcel = Parcel.objects.create(
            plan="ABCDE",
            tenure="Freehold",
            shire_name="Test Shire",
            feature_name="Test Feature",
            alias_name="Test Alias",
            locality="Test Locality",
            parcel_type="Test Parcel Type",
            cover_type="Test Cover",
            accuracy_code="Test Accuracy Code",
            smis_map="Test SMIS Map",
            geometry="POINT(0 0)"
        )
        self.assertIsNone(parcel.lot)