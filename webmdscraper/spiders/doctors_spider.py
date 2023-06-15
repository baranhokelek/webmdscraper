import scrapy


class DoctorSpider(scrapy.Spider):
    name = "doctor-spider"

    def __init__(self, *args, **kwargs):
        with open("./data/page_urls.txt", "r") as pagefile:
            self.start_urls = [line.rstrip() for line in pagefile][:10]

    def parse(self, response, **kwargs):
        request_url_split = response.request.url.split("/")
        for doctor in response.css('div.webmd-card__body')[6:-2]:
            metadata = {
                "name": doctor.css('a.prov-name').css('h2::text').get().strip(),
                "specialty": doctor.css('p.prov-specialty::text').get(),
                "state": request_url_split[-2],
                "link": doctor.css('a.prov-name::attr(href)').get(),
            }
            yield scrapy.Request(metadata["link"], callback=self.get_doctor_website_info, meta=metadata)

    def get_doctor_website_info(self, response):
        name = response.meta["name"]
        specialty = response.meta["specialty"]
        state = response.meta["state"].capitalize()
        link = response.meta["link"]
        website_data = {}
        conditions_treated = response.css('div.profile-basecard.conditions-container').css('div[data-profilecontent*="condition"]').css('a::text').getall()
        hospital_affiliations = response.css('div.profile-basecard.conditions-container').css('div[data-profilecontent*="hospital"]').css('a::text').getall()
        website_data["Name"] = name
        website_data["Specialties"] = specialty
        website_data["State"] = state
        website_data["Link"] = link
        website_data["Conditions Treated"] = conditions_treated
        website_data["Hospital Affiliations"] = hospital_affiliations
        locations_raw = response.css('div.location.loc-coi-locatn.webmd-row')
        for location_raw in locations_raw:
            location = {}
            name = "unknown"
            address = "unknown"
            clinic_phone = "unknown"
            website = "unknown"

            name_field = location_raw.css('div.location-practice-name.loc-coi-pracna.webmd-row')
            name = name_field.css('a::text').get()
            if name is not None:
                name = name.strip()
                location["Name"] = name
                # get address of clinic
                address_line_1 = location_raw.css('div.location-address.loc-coi-locad.webmd-row::text').get()
                address_line_2 = ''.join(location_raw.css('div.location-geo.webmd-row').css('span::text').getall())
                address = address_line_1 + "," + address_line_2
                location["Address"] = address
                # get phone of clinic (if exists)
                clinic_phone = location_raw.css('div.location-phone.webmd-row').css('a::text').get()
                if clinic_phone is None:
                    clinic_phone = ""
                location["Phone"] = clinic_phone
                # get website of clinic (if exists)
                website = location_raw.css('a.site-exit-modal.loc-coi-webs::attr(href)').get()
                if website is None:
                    website = name_field.css("a.loc-coi-pracna::attr(href)").get()
                if website is None:
                    website = ""
                location["Website"] = website
            else:
                location = " ".join(location_raw.css('div::text').getall() + location_raw.css('a::text').getall() + location_raw.css('span::text').getall())
            if "Locations" not in website_data:
                website_data["Locations"] = [location]
            else:
                website_data["Locations"].append(location)
        yield website_data
