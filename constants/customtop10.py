# MIT License
# 
# Copyright (c) 2020 AtishaRibeiro
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

DEFAULT_MII = [0x80, 0x00, 0x00, 0x50, 0x00, 0x6c, 0x00, 0x61, 
    0x00, 0x79, 0x00, 0x65, 0x00, 0x72, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x85, 0x41, 0x9F, 0x4B, 0x00, 0x04, 0x42, 0x40,
    0x31, 0xBD, 0x28, 0xA2, 0x08, 0x8C, 0x08, 0x40,
    0x14, 0x49, 0xB8, 0x8D, 0x00, 0x8A, 0x00, 0x8A, 0x25, 0x04]

class IsoCode:
    __slots__ = ("flag_changer", "globe_position", "custom_title", "top_10", "bypass_crc", "highlight")

    def __init__(self, flag_changer, globe_position, custom_title, top_10, bypass_crc, highlight):
        self.flag_changer = flag_changer
        self.globe_position = globe_position
        self.custom_title = custom_title
        self.top_10 = top_10
        self.bypass_crc = bypass_crc
        self.highlight = highlight

custom_top_10_region_dependent_codes = {
    # [flag changer, globe position, custom title, top 10, bypass crc, highlight]
    # [0,            1,              2,            3,      4,          5]
    "PAL": IsoCode("0242ABD8", "0442BBDC", "C25CDDCC", "C260BFAC", "040C997C", "C263DC48"),
    "NTSC-U": IsoCode("02426858", "0442785C", "C25C12AC", "C26414CC", "040C98DC", "C260C828"),
    "NTSC-J": IsoCode("0242A558", "0442B55C", "C25CD6A8", "C260B720", "040C989C", "C263D2B4"),
    "NTSC-K": IsoCode("02418BF8", "04419BFC", "C25BBD8C", "C25FA3CC", "040C99DC", "C262BF60"),
}

# [country_name, country_code, globe_position, flag_code]
# all countries and regions from the extended regions by Atlas
# locations were taken from Vega's database, a lot are still missing so feel free to fill them in

class Country:
    __slots__ = ("name", "code", "globe_position", "flag_id")

    def __init__(self, name, code, globe_position, flag_id):
        self.name = name
        self.code = code
        self.globe_position = globe_position
        self.flag_id = flag_id

COUNTRIES = [
    Country("NO FLAG", 255, "", ""),
    Country("Japan", 1, "19606363", "JP"),
    Country("Antarctica", 2, "", "AQ"),
    Country("Caribbean Netherlands", 3, "", "NL"),
    Country("FalkLand Islands", 4, "", "FK"),
    Country("Scotland", 5, "27CAFDB9", "GB"),
    Country("Wales", 6, "249BFDBE", "GB"),
    Country("Sint Maarten", 7, "", "SX"),
    Country("Anguilla", 8, "0CF4D32B", "AI"),
    Country("Antigua and Barbuda", 9, "0C2BD405", "AG"),
    Country("Argentina", 10, "E729D6CB", "AR"),
    Country("Aruba", 11, "08E6CE33", "AW"),
    Country("Bahamas", 12, "11D6C8FF", "BS"),
    Country("Barbados", 13, "0950D59C", "BB"),
    Country("Belize", 14, "0C44C0E1", "BZ"),
    Country("Bolivia", 15, "F445CF8A", "BO"),
    Country("Brazil", 16, "EFB8E142", "BR"),
    Country("British Virgin Islands", 17, "0D18D20D", "VG"),
    Country("Canada", 18, "2379BAEB", "CA"),
    Country("Cayman Islands", 19, "0DB9C621", "KY"),
    Country("Chile", 20, "E837CDC0", "CL"),
    Country("Colombia", 21, "0305CB40", "CO"),
    Country("Costa Rica", 22, "0710C436", "CR"),
    Country("Dominica", 23, "0AE1D457", "DM"),
    Country("Dominican Republic", 24, "0D21CE4C", "DO"),
    Country("Ecuador", 25, "FFD9C82E", "EC"),
    Country("El Salvador", 26, "09BFC092", "SV"),
    Country("French Guiana", 27, "0382DACA", "GF"),
    Country("Grenada", 28, "0891D417", "GD"),
    Country("Guadeloupe", 29, "0B60D41D", "GP"),
    Country("Guatemala", 30, "0A65BFA1", "GT"),
    Country("Guyana", 31, "04D5D6A4", "GY"),
    Country("Haiti", 32, "0D2ECC90", "HT"),
    Country("Honduras", 33, "0A06C1FB", "HN"),
    Country("Jamaica", 34, "0CCCC963", "JM"),
    Country("Martinique", 35, "0A61D491", "MQ"),
    Country("Mexico", 36, "0DB7B921", "MX"),
    Country("Montserrat", 37, "0BE0D3C2", "MS"),
    Country("Netherlands Antilles", 38, "089ACEFF", "AN"),
    Country("Nicaragua", 39, "08A3C2A8", "NI"),
    Country("Panama", 40, "0660C772", "PA"),
    Country("Paraguay", 41, "EE09D6FF", "PY"),
    Country("Peru", 42, "F76FC936", "PE"),
    Country("St. Kitts and Nevis", 43, "0C4DD367", "KN"),
    Country("St. Lucia", 44, "09F4D4A0", "LC"),
    Country("St. Vincent and Grenadines", 45, "0956D478", "VC"),
    Country("Suriname", 46, "0425D8C6", "SR"),
    Country("Trinidad and Tobago", 47, "0792D442", "TT"),
    Country("Turks and Caicos Islands", 48, "0F43CD6B", "TC"),
    Country("USA", 49, "1BC4BBF7", "US"),
    Country("Uruguay", 50, "E737D80F", "UY"),
    Country("U.S. Virgin Islands", 51, "0D0BD1D4", "VI"),
    Country("Venezuela", 52, "0777D06B", "VE"),
    Country("Armenia", 53, "", "AM"),
    Country("Belarus", 54, "", "BY"),
    Country("Georgia", 55, "", "GE"),
    Country("Kosovo", 56, "1E540F0B", "XK"),
    Country("Abkhazia", 57, "", "AK"),
    Country("Artsakh", 58, "", "AH"),
    Country("Northern Cyprus", 59, "190117BB", "NY"),
    Country("South Ossetia", 60, "", ""),
    Country("Transnistria", 61, "", ""),
    Country("Åland", 62, "", "AX"),
    Country("Faroe Islands", 63, "", "FO"),
    Country("Albania", 64, "1D630E19", "AL"),
    Country("Australia", 65, "E72C6291", "AU"),
    Country("Austria", 66, "22470BA4", "AT"),
    Country("Belgium", 67, "2427031B", "BE"),
    Country("Bosnia and Herzegovina", 68, "1F2F0D17", "BA"),
    Country("Botswana", 69, "EE79126B", "BW"),
    Country("Bulgaria", 70, "1E5E1092", "BG"),
    Country("Croatia", 71, "20920B5A", "HR"),
    Country("Cyprus", 72, "190117BB", "CY"),
    Country("Czechia", 73, "239B0A43", "CZ"),
    Country("Denmark", 74, "279A08ED", "DK"),
    Country("Estonia", 75, "2A431196", "EE"),
    Country("Finland", 76, "2AC911BB", "FI"),
    Country("France", 77, "22BD01AB", "FR"),
    Country("Germany", 78, "25590988", "DE"),
    Country("Greece", 79, "1B0110DE", "GR"),
    Country("Hungary", 80, "21C50D91", "HU"),
    Country("Iceland", 81, "2D9BF06F", "IS"),
    Country("Ireland", 82, "25EEFB8D", "IE"),
    Country("Italy", 83, "1DCA08E1", "IT"),
    Country("Latvia", 84, "287F1120", "LV"),
    Country("Lesotho", 85, "EB271388", "LS"),
    Country("Liechtenstein", 86, "218506C5", "LI"),
    Country("Lithuania", 87, "26E211FA", "LT"),
    Country("Luxembourg", 88, "2347045B", "LU"),
    Country("North Macedonia", 89, "1DDE0F40", "MK"),
    Country("Malta", 90, "19870A52", "MT"),
    Country("Montenegro", 91, "", "ME"),
    Country("Mozambique", 92, "ED891728", "MZ"),
    Country("Namibia", 93, "EFF70C25", "NA"),
    Country("Netherlands", 94, "253D0379", "NL"),
    Country("New Zealand", 95, "E29F7C4A", "NZ"),
    Country("Norway", 96, "2A9F079D", "NO"),
    Country("Poland", 97, "25260EF0", "PL"),
    Country("Portugal", 98, "1B89F980", "PT"),
    Country("Romania", 99, "1F98128C", "RO"),
    Country("Russia", 100, "27A81ABF", "RU"),
    Country("Serbia", 101, "1FE10E91", "RS"),
    Country("Slovakia", 102, "223D0C2D", "SK"),
    Country("Slovenia", 103, "20BF0A50", "SI"),
    Country("South Africa", 104, "ED6913F2", "ZA"),
    Country("Spain", 105, "1CBDFD5E", "ES"),
    Country("Eswatini", 106, "ED491624", "SZ"),
    Country("Sweden", 107, "2A280CDA", "SE"),
    Country("Switzerland", 108, "21630546", "CH"),
    Country("Turkey", 109, "1C64175C", "TR"),
    Country("United Kingdom", 110, "24A0FFEB", "GB"),
    Country("Zambia", 111, "F50A141C", "ZM"),
    Country("Zimbabwe", 112, "F3541614", "ZW"),
    Country("Azerbaijan", 113, "1CB6237A", "AZ"),
    Country("Mauritania", 114, "0CDFF4A9", "MR"),
    Country("Mali", 115, "08FEFA50", "ML"),
    Country("Niger", 116, "099D017F", "NE"),
    Country("Chad", 117, "089C0AB1", "TD"),
    Country("Sudan", 118, "0B1D1722", "SD"),
    Country("Eritrea", 119, "0AE71BAF", "ER"),
    Country("Djibouti", 120, "083D1EAE", "DJ"),
    Country("Somalia", 121, "0172203F", "SO"),
    Country("Andorra", 122, "", "AD"),
    Country("Gibraltar", 123, "", "GI"),
    Country("Guernsey", 124, "", "GG"),
    Country("Isle of Man", 125, "2684FCD0", "IM"),
    Country("Jersey", 126, "", "JE"),
    Country("Monaco", 127, "", "MC"),
    Country("Taiwan", 128, "11CD5667", "TW"),
    Country("Cambodia", 129, "", "KH"),
    Country("Laos", 130, "", "LA"),
    Country("Mongolia", 131, "", "MN"),
    Country("Myanmar", 132, "", "MM"),
    Country("Nepal", 133, "", "NP"),
    Country("Vietnam", 134, "", "VN"),
    Country("North Korea", 135, "", "KP"),
    Country("South Korea", 136, "1AAA5A4F", "KR"),
    Country("Bangladesh", 137, "", "BD"),
    Country("Bhutan", 138, "", "BT"),
    Country("Brunei", 139, "", "BN"),
    Country("Maldives", 140, "", "MV"),
    Country("Sri Lanka", 141, "", "LK"),
    Country("Timor-Leste", 142, "", "TL"),
    Country("British Indian Ocean Territory", 143, "", "IO"),
    Country("Hong Kong", 144, "0FF95147", "HK"),
    Country("Macao", 145, "0FCC50C8", "MO"),
    Country("Cook Islands", 146, "", "CK"),
    Country("Niue", 147, "", "NU"),
    Country("Norfolk Island", 148, "", "NF"),
    Country("Northern Mariana Islands", 149, "", "MP"),
    Country("American Samoa", 150, "", "AS"),
    Country("Guam", 151, "", "GU"),
    Country("Indonesia", 152, "FB9C4BF7", "ID"),
    Country("Singapore", 153, "00EB49DA", "SG"),
    Country("Thailand", 154, "09C7477A", "TH"),
    Country("Philippines", 155, "0A625608", "PH"),
    Country("Malaysia", 156, "02404851", "MY"),
    Country("St. Barthélemy", 157, "", "BL"),
    Country("St. Martin", 158, "", "MF"),
    Country("St. Pierre and Miquelon", 159, "", "PM"),
    Country("China", 160, "1C6252CC", "CN"),
    Country("Afghanistan", 161, "", "AF"),
    Country("Kazakhstan", 162, "", "KZ"),
    Country("Kyrgyzstan", 163, "", "KG"),
    Country("Pakistan", 164, "", "PK"),
    Country("Tajikistan", 165, "", "TJ"),
    Country("Turkmenistan", 166, "", "TM"),
    Country("Uzbekistan", 167, "", "UZ"),
    Country("United Arab Emirates", 168, "116626A9", "AE"),
    Country("India", 169, "145636E5", "IN"),
    Country("Egypt", 170, "155E1638", "EG"),
    Country("Oman", 171, "10CA29AA", "OM"),
    Country("Qatar", 172, "11FB24A5", "QA"),
    Country("Kuwait", 173, "14E2221E", "KW"),
    Country("Saudi Arabia", 174, "11852142", "SA"),
    Country("Syria", 175, "17D219D0", "SY"),
    Country("Bahrain", 176, "12A823F8", "BH"),
    Country("Jordan", 177, "16B8198D", "JO"),
    Country("Iran", 178, "", "IR"),
    Country("Iraq", 179, "", "IQ"),
    Country("Israel", 180, "", "IL"),
    Country("Lebanon", 181, "", "LB"),
    Country("Palestine", 182, "", "PS"),
    Country("Yemen", 183, "", "YE"),
    Country("San Marino", 184, "", "SM"),
    Country("Vatican City", 185, "", "VS"),
    Country("Bermuda", 186, "", "BM"),
    Country("French Polynesia", 187, "", "PF"),
    Country("Réunion", 188, "", "RE"),
    Country("Mayotte", 189, "", "YT"),
    Country("New Caledonia", 190, "", "NC"),
    Country("Wallis and Futuna", 191, "", "WF"),
    Country("Nigeria", 192, "", "NG"),
    Country("Angola", 193, "", "AO"),
    Country("Ghana", 194, "", "GH"),
    Country("Togo", 195, "", "TG"),
    Country("Benin", 196, "", "BJ"),
    Country("Burkina Faso", 197, "", "BF"),
    Country("Côte d'Ivoire", 198, "", "CI"),
    Country("Liberia", 199, "", "LR"),
    Country("Sierra Leone", 200, "", "SL"),
    Country("Guinea", 201, "", "GN"),
    Country("Guinea-Bissau", 202, "", "GW"),
    Country("Senegal", 203, "", "SN"),
    Country("The Gambia", 204, "", "GM"),
    Country("Cape Verde", 205, "", "CV"),
    Country("St. Helena, Ascension and Tristan da Cunha", 206, "", "SH"),
    Country("Moldova", 207, "", "MD"),
    Country("Ukraine", 208, "", "UA"),
    Country("Cameroon", 209, "", "CM"),
    Country("Central African Republic", 210, "", "CF"),
    Country("Democratic Republic of the Congo", 211, "", "CD"),
    Country("Republic of the Congo", 212, "", "CG"),
    Country("Equatorial Guinea", 213, "F50A141C", "GQ"),
    Country("Gabon", 214, "", "GA"),
    Country("São Tomé and Príncipe", 215, "", "ST"),
    Country("Algeria", 216, "", "DZ"),
    Country("Ethiopia", 217, "", "ET"),
    Country("Libya", 218, "", "LY"),
    Country("Morocco", 219, "", "MA"),
    Country("South Sudan", 220, "", "SS"),
    Country("Tunisia", 221, "", "TN"),
    Country("Sahrawi Arab Democratic Republic", 222, "", "EH"),
    Country("Cuba", 223, "", "CU"),
    Country("Burundi", 224, "", "BI"),
    Country("Comoros", 225, "", "KM"),
    Country("Kenya", 226, "", "KE"),
    Country("Madagascar", 227, "", "MG"),
    Country("Malawi", 228, "", "MW"),
    Country("Mauritius", 229, "", "MU"),
    Country("Rwanda", 230, "", "RW"),
    Country("Seychelles", 231, "", "SC"),
    Country("Tanzania", 232, "", "TZ"),
    Country("Uganda", 233, "", "UG"),
    Country("French Southern and Antarctic Lands", 234, "", "FR"),
    Country("Pitcairn Islands", 235, "", "PN"),
    Country("British Antarctic Territory", 236, "", "GB"),
    Country("South Georgia and the South Sandwich Islands", 237, "", "GS"),
    Country("Federated States of Micronesia", 238, "", "FM"),
    Country("Fiji", 239, "", "FJ"),
    Country("Kiribati", 240, "", "KI"),
    Country("Marshall Islands", 241, "", "MH"),
    Country("Nauru", 242, "", "NR"),
    Country("Palau", 243, "", "PW"),
    Country("Papua New Guinea", 244, "", "PG"),
    Country("Samoa", 245, "", "WS"),
    Country("Solomon Islands", 246, "", "SB"),
    Country("Tokelau", 247, "", "TK"),
    Country("Tonga", 248, "", "TO"),
    Country("Tuvalu", 249, "", "TV"),
    Country("Vanuatu", 250, "", "VU"),
    Country("Christmas Island", 251, "", "CX"),
    Country("Cocos (Keeling) Islands", 252, "", "CC"),
    Country("Puerto Rico", 253, "0D22D0FE", "PR"),
    Country("Greenland", 254, "2DA4DB39", "GL"),
]

def create_countries_by_x_table(countries, key):
    countries_by_x = {}

    for country in countries:
        key_value = getattr(country, key)
        if key_value != "":
            countries_by_x[key_value] = country

    return countries_by_x

countries_by_name = create_countries_by_x_table(COUNTRIES, "name")
countries_by_code = create_countries_by_x_table(COUNTRIES, "code")
countries_by_flag_id = create_countries_by_x_table(COUNTRIES, "flag_id")
