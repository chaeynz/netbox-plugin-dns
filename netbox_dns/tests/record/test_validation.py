from django.test import TestCase
from django.core.exceptions import ValidationError

from netbox_dns.models import Zone, Record, RecordTypeChoices, NameServer


class RecordValidationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        zone_data = {
            "soa_mname": NameServer.objects.create(name="ns1.example.com"),
            "soa_rname": "hostmaster.example.com",
        }

        cls.zones = [
            Zone(name="zone1.example.com", **zone_data),
            Zone(name="1.0.10.in-addr.arpa", **zone_data),
            Zone(name="1.0.0.0.f.e.e.b.d.a.e.d.0.8.e.f.ip6.arpa", **zone_data),
        ]
        for zone in cls.zones:
            zone.save()

    def test_create_record_validation_ok(self):
        zone = self.zones[0]

        ok_records = [
            {"name": "test1", "type": RecordTypeChoices.A, "value": "10.0.1.42"},
            {"name": "test2", "type": RecordTypeChoices.A, "value": "10.0.2.42"},
            {
                "name": "test3",
                "type": RecordTypeChoices.AAAA,
                "value": "fe80:dead:beef::1:42",
            },
            {
                "name": "test4",
                "type": RecordTypeChoices.AAAA,
                "value": "fe80:dead:beef::2:42",
            },
            {
                "name": "test5",
                "type": RecordTypeChoices.MX,
                "value": "10 mx1.example.com",
            },
            {
                "name": "test6",
                "type": RecordTypeChoices.MX,
                "value": "10 mx1.example.com.",
            },
            {
                "name": "test8",
                "type": RecordTypeChoices.CAA,
                "value": "1 issue example.org",
            },
            {"name": "test9", "type": RecordTypeChoices.CNAME, "value": "test1"},
        ]

        for record in ok_records:
            Record.objects.create(zone=zone, **record)

    def test_create_record_validation_fail(self):
        zone = self.zones[0]

        broken_records = [
            {"name": "test1", "type": RecordTypeChoices.A, "value": "1.1.1.1.1"},
            {"name": "test2", "type": RecordTypeChoices.A, "value": "1.1.1"},
            {"name": "test3", "type": RecordTypeChoices.A, "value": "1.1.1.256"},
            {
                "name": "test4",
                "type": RecordTypeChoices.A,
                "value": "fe80:dead:beef:1:42:1111:2222:3333:4444",
            },
            {
                "name": "test5",
                "type": RecordTypeChoices.A,
                "value": "fe80:dead:beef:1:42:1111:2222",
            },
            {
                "name": "test6",
                "type": RecordTypeChoices.A,
                "value": "fe80:dead:beer:1:42:1111:2222:3333",
            },
            {"name": "test7", "type": RecordTypeChoices.AAAA, "value": "1.1.1.1.1"},
            {"name": "test8", "type": RecordTypeChoices.AAAA, "value": "1.1.1"},
            {"name": "test9", "type": RecordTypeChoices.AAAA, "value": "1.1.1.256"},
            {
                "name": "test10",
                "type": RecordTypeChoices.AAAA,
                "value": "fe80:dead:beef:42:1111:2222:3333:4444:5555",
            },
            {
                "name": "test11",
                "type": RecordTypeChoices.AAAA,
                "value": "fe80:dead:beef:42:1111:2222:3333",
            },
            {
                "name": "test12",
                "type": RecordTypeChoices.AAAA,
                "value": "fe80:dead:beer:42:1111:2222:3333:4444",
            },
            {
                "name": "test13",
                "type": RecordTypeChoices.MX,
                "value": "1000000 mx1.example.com",
            },
            {
                "name": "test13",
                "type": RecordTypeChoices.MX,
                "value": "1000000 1.1.1.1",
            },
            {
                "name": "test14",
                "type": RecordTypeChoices.SOA,
                "value": "(ns1.example.com. hostmaster.example.com. 1651498477 172800 7200 2592000)",
            },
            {
                "name": "test15",
                "type": RecordTypeChoices.SOA,
                "value": "(ns1.example.com. 1651498477 172800 7200 2592000 3600)",
            },
            {
                "name": "test16",
                "type": RecordTypeChoices.SOA,
                "value": "(ns1.example.com. hostmaster.example.com. -1 172800 7200 2592000 3600)",
            },
            {
                "name": "test17",
                "type": RecordTypeChoices.SOA,
                "value": "(ns1.example.com. hostmaster.example.com. claptrap 172800 7200 2592000 3600)",
            },
            {"name": "test18", "type": RecordTypeChoices.CAA, "value": "1"},
            {"name": "test19", "type": RecordTypeChoices.CAA, "value": "issue"},
            {"name": "test20", "type": RecordTypeChoices.CAA, "value": "1 issue"},
            {
                "name": "test21",
                "type": RecordTypeChoices.CAA,
                "value": "1 issue example.org claptrap",
            },
            {
                "name": "test22",
                "type": RecordTypeChoices.CNAME,
                "value": "test1 claptrap",
            },
        ]

        for record in broken_records:
            with self.assertRaises(ValidationError):
                Record.objects.create(zone=zone, **record)

    def test_name_and_cname(self):
        zone = self.zones[0]

        name1 = "test1"
        name2 = "test2"
        address = "fe80:dead:beef:1::42"

        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.AAAA,
            value=address,
        )

        with self.assertRaises(ValidationError):
            Record.objects.create(
                zone=zone,
                name=name1,
                type=RecordTypeChoices.CNAME,
                value=name2,
            )

    def test_nsec_and_cname(self):
        zone = self.zones[0]

        name1 = "test1"
        name2 = "test2"

        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.NSEC,
            value="test2.zone1.example.com. A MX RRSIG NSEC",
        )
        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.CNAME,
            value=name2,
        )

        self.assertEqual(Record.objects.filter(name=name1, zone=zone).count(), 2)

    def test_cname_and_name(self):
        zone = self.zones[0]

        name1 = "test1"
        name2 = "test2"
        address = "fe80:dead:beef:1::42"

        Record.objects.create(
            zone=zone, name=name1, type=RecordTypeChoices.CNAME, value=name2
        )

        with self.assertRaises(ValidationError):
            Record.objects.create(
                zone=zone, name=name1, type=RecordTypeChoices.AAAA, value=address
            )

    def test_cname_and_nsec(self):
        zone = self.zones[0]

        name1 = "test1"
        name2 = "test2"

        Record.objects.create(
            zone=zone, name=name1, type=RecordTypeChoices.CNAME, value=name2
        )
        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.NSEC,
            value="test2.zone1.example.com. A MX RRSIG NSEC",
        )

        self.assertEqual(Record.objects.filter(name=name1, zone=zone).count(), 2)

    def test_double_singletons(self):
        zone = self.zones[1]

        name1 = "test1"
        name2 = "test2"
        name3 = "test3"

        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.DNAME,
            value=name2,
        )

        with self.assertRaises(ValidationError):
            Record.objects.create(
                zone=zone,
                name=name1,
                type=RecordTypeChoices.DNAME,
                value=name3,
            )

    def test_inactive_name_and_active_cname(self):
        zone = self.zones[0]

        name1 = "test1"
        name2 = "test2"
        address = "fe80:dead:beef:1::42"

        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.AAAA,
            value=address,
            status="inactive",
        )
        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.CNAME,
            value=name2,
        )

    def test_inactive_cname_and_active_name(self):
        zone = self.zones[0]

        name1 = "test1"
        name2 = "test2"
        address = "fe80:dead:beef:1::42"

        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.CNAME,
            value=name2,
            status="inactive",
        )
        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.AAAA,
            value=address,
        )

    def test_double_singletons_inactive_active(self):
        zone = self.zones[1]

        name1 = "test1"
        name2 = "test2"
        name3 = "test3"

        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.DNAME,
            value=name2,
            status="inactive",
        )
        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.DNAME,
            value=name3,
        )

    def test_active_name_and_inactive_cname(self):
        zone = self.zones[0]

        name1 = "test1"
        name2 = "test2"
        address = "fe80:dead:beef:1::42"

        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.AAAA,
            value=address,
        )
        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.CNAME,
            value=name2,
            status="inactive",
        )

    def test_active_cname_and_inactive_name(self):
        zone = self.zones[0]

        name1 = "test1"
        name2 = "test2"
        address = "fe80:dead:beef:1::42"

        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.CNAME,
            value=name2,
        )
        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.AAAA,
            value=address,
            status="inactive",
        )

    def test_double_singletons_active_inactive(self):
        zone = self.zones[1]

        name1 = "test1"
        name2 = "test2"
        name3 = "test3"

        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.DNAME,
            value=name2,
        )
        Record.objects.create(
            zone=zone,
            name=name1,
            type=RecordTypeChoices.DNAME,
            value=name3,
            status="inactive",
        )

    def test_lowercase_type(self):
        f_zone1 = self.zones[0]
        r_zone1 = self.zones[1]
        r_zone2 = self.zones[2]

        records = [
            {"zone": f_zone1, "name": "name1", "type": "a", "value": "10.0.1.1"},
            {
                "zone": f_zone1,
                "name": "name2",
                "type": "aaaa",
                "value": "fe80:dead:beef:42::1",
            },
            {
                "zone": f_zone1,
                "name": "name3",
                "type": "aAaA",
                "value": "fe80:dead:beef:42::2",
            },
            {"zone": f_zone1, "name": "name4", "type": "cname", "value": "name101"},
            {
                "zone": r_zone1,
                "name": "3",
                "type": "pTr",
                "value": "name3.example.com.",
            },
            {
                "zone": r_zone2,
                "name": "1.0.0.0.2.4.0.0.0.0.0.0.0.0.0.0",
                "type": "ptr",
                "value": "name2.example.com.",
            },
        ]

        for record in records:
            Record.objects.create(**record)

            test_record = Record.objects.get(zone=record["zone"], name=record["name"])
            self.assertEqual(test_record.type, record["type"].upper())

    def test_valid_name_in_value(self):
        f_zone = self.zones[0]
        r_zone = self.zones[2]

        records = (
            Record(
                name="name1",
                zone=f_zone,
                type=RecordTypeChoices.CNAME,
                value="name2.zone1.example.com.",
            ),
            Record(
                name="name2", zone=f_zone, type=RecordTypeChoices.CNAME, value="name2"
            ),
            Record(
                name="name3",
                zone=f_zone,
                type=RecordTypeChoices.DNAME,
                value="zone2.example.com.",
            ),
            Record(
                name="name4",
                zone=f_zone,
                type=RecordTypeChoices.HTTPS,
                value="0 www.example.com.",
            ),
            Record(
                name="name5",
                zone=f_zone,
                type=RecordTypeChoices.KX,
                value="10 name1.example.com.",
            ),
            Record(
                name="name6",
                zone=f_zone,
                type=RecordTypeChoices.MX,
                value="10 mx1.example.com.",
            ),
            Record(
                name="name7",
                zone=f_zone,
                type=RecordTypeChoices.NS,
                value="ns1.example.com.",
            ),
            Record(
                name="name8",
                zone=f_zone,
                type=RecordTypeChoices.NAPTR,
                value='100 10 "S" "SIP+D2U" "!^.*$!sip:customer-service@example.com!" _sip._udp.example.com.',
            ),
            Record(
                name="67894444333322220000",
                zone=f_zone,
                type=RecordTypeChoices.NSAP_PTR,
                value="name1.example.com.",
            ),
            Record(
                name="name10",
                zone=f_zone,
                type=RecordTypeChoices.NSEC,
                value="name11.zone_1.example.com.",
            ),
            Record(
                name="1",
                zone=r_zone,
                type=RecordTypeChoices.PTR,
                value="name11.example.com.",
            ),
            Record(
                name="name12",
                zone=f_zone,
                type=RecordTypeChoices.RP,
                value="admin.zone1.example.com. info.zone1.example.com.",
            ),
            Record(
                name="name13",
                zone=f_zone,
                type=RecordTypeChoices.RT,
                value="10 name99.zone1.example.com.",
            ),
            Record(
                name="name14",
                zone=f_zone,
                type=RecordTypeChoices.PX,
                value="10 name10.zone1.example.com. name_11.zone1.example.com.",
            ),
            Record(
                name="name15",
                zone=f_zone,
                type=RecordTypeChoices.SRV,
                value="10 60 443 name2.zone1.example.com.",
            ),
            Record(
                name="name16",
                zone=f_zone,
                type=RecordTypeChoices.SVCB,
                value="1 svc.example.com.",
            ),
        )

        for record in records:
            record.save()

    def test_invalid_name_in_value(self):
        f_zone = self.zones[0]
        r_zone = self.zones[2]

        records = (
            Record(
                name="name1",
                zone=f_zone,
                type=RecordTypeChoices.CNAME,
                value="xn--bb.zone1.example.com.",
            ),
            Record(
                name="name2", zone=f_zone, type=RecordTypeChoices.CNAME, value="aa--bb"
            ),
            Record(
                name="name3",
                zone=f_zone,
                type=RecordTypeChoices.DNAME,
                value="f#ck&&%%.example.com.",
            ),
            Record(
                name="name4",
                zone=f_zone,
                type=RecordTypeChoices.HTTPS,
                value="0 [].example.com.",
            ),
            Record(
                name="name5",
                zone=f_zone,
                type=RecordTypeChoices.KX,
                value="10 xn--bb.example.com.",
            ),
            Record(
                name="name6",
                zone=f_zone,
                type=RecordTypeChoices.MX,
                value="10 bla*.example.com.",
            ),
            Record(
                name="name7",
                zone=f_zone,
                type=RecordTypeChoices.NS,
                value="[#^$[¨}!;--_?:.@/\ˇ´%].example.com.",
            ),
            Record(
                name="name8",
                zone=f_zone,
                type=RecordTypeChoices.NAPTR,
                value='100 10 "S" "SIP+D2U" "!^.*$!sip:customer-service@example.com!" _sip._udp.xn--bb.com.',
            ),
            Record(
                name="67894444333322220000",
                zone=f_zone,
                type=RecordTypeChoices.NSAP_PTR,
                value="name1.xn--bb.com.",
            ),
            Record(
                name="name10",
                zone=f_zone,
                type=RecordTypeChoices.NSEC,
                value="name11.[#^$[¨}!;--_?:.@/\ˇ´%].example.com.",
            ),
            Record(
                name="1",
                zone=r_zone,
                type=RecordTypeChoices.PTR,
                value="name11.[#^$[¨}!;--_?:.@/\ˇ´%].com.",
            ),
            Record(
                name="name12",
                zone=f_zone,
                type=RecordTypeChoices.RP,
                value="admin.aa--bb.example.com. info.zone1.example.com.",
            ),
            Record(
                name="name13",
                zone=f_zone,
                type=RecordTypeChoices.RP,
                value="admin.example.com. xn--bb.zone1.example.com.",
            ),
            Record(
                name="name14",
                zone=f_zone,
                type=RecordTypeChoices.RT,
                value="10 name99.[#^$[¨}!;--_?:.@/\ˇ´%].example.com.",
            ),
            Record(
                name="name15",
                zone=f_zone,
                type=RecordTypeChoices.PX,
                value="10 name10.zo--ne1.example.com. name11.zone1.example.com.",
            ),
            Record(
                name="name16",
                zone=f_zone,
                type=RecordTypeChoices.PX,
                value="10 name10.zone1.example.com. na--me11.zone1.example.com.",
            ),
            Record(
                name="name17",
                zone=f_zone,
                type=RecordTypeChoices.SRV,
                value="10 60 443 [#^$[¨}!;--_?:.@/\ˇ´%].zone1.example.com.",
            ),
            Record(
                name="name18",
                zone=f_zone,
                type=RecordTypeChoices.SVCB,
                value="1 svc.[#^$[¨}!;--_?:.@/\ˇ´%].com.",
            ),
        )

        for record in records:
            with self.assertRaises(ValidationError):
                record.save()
