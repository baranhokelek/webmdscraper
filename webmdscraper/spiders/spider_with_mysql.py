import scrapy
import mysql.connector

# This file is for demonstration only. This code is not used for the actual scraping job.


class MySpider(scrapy.Spider):
    name = "example_spider"

    start_urls = ["https://doctor.webmd.com/providers/arizona"]

    # def parse(self, response):
    #     state_urls = response.css('a.state-name::attr(href)').getall()
    #     for state_url in state_urls:
    #         yield scrapy.Request(state_url, callback=self.parse_states)

    def parse(self, response):
        state = response.request.url.split("/")[-1]
        set_sql(state)
        city_urls = response.css('ul.centerwell-list.all-cities').css('a::attr(href)').getall()
        # city_urls_compact = response.css('ul.centerwell-list.mob-initial-list').css('a::attr(href)').getall()
        for city_url in city_urls:
            yield scrapy.Request(city_url, callback=self.parse_cities)

    def parse_cities(self, response):
        # Extract data from the webpage and insert into the database
        data = response.css('div.webmd-card__body')[6:-2]
        request_url_split = response.request.url.split("/")
        city = request_url_split[-1].split("?")[0]
        state = request_url_split[-2]
        num_pages = response.css('a.number::text')
        if num_pages is None or len(num_pages) == 0:
            last_page = 1
        else:
            last_page = int(num_pages[-1].get())
        current_url = response.request.url
        if "pagenumber" not in current_url:
            page_number = 1
        else:
            page_number = int(list(current_url.partition("pagenumber="))[-1])
        if page_number <= last_page:  # if there is a next page (TEST: limit to first 10 pages for each city)
            if "pagenumber" not in current_url:
                next_page = current_url + "?pagenumber=2"
            else:
                partitioned_url = list(current_url.partition("pagenumber="))
                page_number = int(partitioned_url[-1])
                partitioned_url[-1] = str(page_number + 1)
                next_page = ''.join(partitioned_url)
            yield response.follow(next_page, callback=self.parse_cities)
        for doctor in data:
            name = doctor.css('a.prov-name').css('h2::text').get().strip()
            specialties = doctor.css('p.prov-specialty::text').get()
            if specialties is not None:
                specialties = specialties.split(",")
            yield scrapy.Request(doctor.css('a.prov-name::attr(href)').get(), callback=self.get_doctor_website_info, meta={"name": name, "city": city, "state": state, "specialties": specialties})

    def get_doctor_website_info(self, response):
        name = response.meta["name"]
        city = response.meta["city"]
        state = response.meta["state"]
        specialties = response.meta["specialties"]
        conditions_treated = response.css('div.profile-basecard.conditions-container').css('div[data-profilecontent*="condition"]').css('a::text').getall()
        locations_raw = response.css('div.location.loc-coi-locatn.webmd-row')
        locations = []
        for location_raw in locations_raw:
            # get name of clinic
            name_field = location_raw.css('div.location-practice-name.loc-coi-pracna.webmd-row')
            loc_name = name_field.css('a::text').get()
            if loc_name is None:
                loc_name = name_field.css('span::text').get()
            if loc_name is None:
                continue
            loc_name = loc_name.strip()

            # get address of clinic
            address_line_1 = location_raw.css('div.location-address.loc-coi-locad.webmd-row::text').get()
            address_line_2 = ''.join(location_raw.css('div.location-geo.webmd-row').css('span::text').getall())
            address = address_line_1 + "," + address_line_2

            # get phone of clinic (if exists)
            clinic_phone = location_raw.css('div.location-phone.webmd-row').css('a::text').get()
            if clinic_phone is None:
                clinic_phone = ""

            # get website of clinic (if exists)
            website = location_raw.css('a.site-exit-modal.loc-coi-webs::attr(href)').get()
            if website is None:
                website = name_field.css("a.loc-coi-pracna::attr(href)").get()
            if website is None:
                website = ""

            locations.append((name, loc_name, address, clinic_phone, website))

        # Establish a connection to the MySQL database
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='hellothere',
            database='sys'
        )
        cursor = conn.cursor()

        # Customize the query and table name according to your schema
        query_doctor = f"INSERT INTO doctors{'_' + state} (name, city, state) VALUES (%s, %s, %s)"
        values = (name, city, state)  # Replace with the actual values extracted
        cursor.execute(query_doctor, values)
        conn.commit()

        if len(conditions_treated) > 0:
            conditions_with_names = [(name, cond) for cond in conditions_treated]
            query_conditions = f"INSERT INTO doctors_conditions{'_' + state} (doctor_name, condition_treated) VALUES (%s, %s)"
            cursor.executemany(query_conditions, conditions_with_names)
            conn.commit()

        if len(specialties) > 0:
            specialties_with_names = [(name, sp.strip()) for sp in specialties]
            query_specialties = f"INSERT INTO doctors_specialties{'_' + state} (doctor_name, specialty) VALUES (%s, %s)"
            cursor.executemany(query_specialties, specialties_with_names)
            conn.commit()

        if len(locations) > 0:
            query_locations = f"INSERT INTO doctors_locations{'_' + state} (doctor_name, location_name, address, phone, website) VALUES (%s, %s, %s, %s, %s)"
            cursor.executemany(query_locations, locations)
            conn.commit()

        # Close the database connection
        cursor.close()
        conn.close()


def reset_sql():
    # Establish a connection to the MySQL database
    conn = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='hellothere',
        database='sys'
    )
    cursor = conn.cursor()

    # clear tables
    query_drop_doctors = "DROP TABLE IF EXISTS doctors"
    query_rebuild_doctors = "CREATE TABLE `doctors` (`id` int NOT NULL AUTO_INCREMENT, `name` varchar(200) DEFAULT NULL, `city` varchar(45) DEFAULT NULL, `state` varchar(45) DEFAULT NULL, PRIMARY KEY (`id`), KEY `nameIdx` (`name`)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
    query_drop_conditions = "DROP TABLE IF EXISTS doctors_conditions"
    query_rebuild_conditions = "CREATE TABLE `doctors_conditions` (`id` int NOT NULL AUTO_INCREMENT, `doctor_name` varchar(200) DEFAULT NULL, `condition_treated` varchar(200) DEFAULT NULL, PRIMARY KEY (`id`), KEY `doctorName_idx` (`doctor_name`), CONSTRAINT `doctorNameConditions` FOREIGN KEY (`doctor_name`) REFERENCES `doctors` (`name`)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
    query_drop_specialties = "DROP TABLE IF EXISTS doctors_specialties"
    query_rebuild_specialties = "CREATE TABLE `doctors_specialties` (`id` int NOT NULL AUTO_INCREMENT, `doctor_name` varchar(200) DEFAULT NULL, `specialty` varchar(200) DEFAULT NULL, PRIMARY KEY (`id`), KEY `doctorName_idx` (`doctor_name`), CONSTRAINT `doctorNameSpecialties` FOREIGN KEY (`doctor_name`) REFERENCES `doctors` (`name`)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
    query_drop_locations = "DROP TABLE IF EXISTS doctors_locations"
    query_rebuild_locations = "CREATE TABLE `doctors_locations` (`id` int NOT NULL AUTO_INCREMENT, `doctor_name` varchar(200) DEFAULT NULL, `location_name` varchar(200) DEFAULT NULL, `address` varchar(200) DEFAULT NULL, `phone` varchar(200) DEFAULT NULL, `website` varchar(200) DEFAULT NULL, PRIMARY KEY (`id`), KEY `doctorName_idx` (`doctor_name`), CONSTRAINT `doctorNameLocations` FOREIGN KEY (`doctor_name`) REFERENCES `doctors` (`name`)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
    cursor.execute(query_drop_conditions)
    conn.commit()
    cursor.execute(query_drop_specialties)
    conn.commit()
    cursor.execute(query_drop_locations)
    conn.commit()
    cursor.execute(query_drop_doctors)
    conn.commit()
    cursor.execute(query_rebuild_doctors)
    conn.commit()
    cursor.execute(query_rebuild_conditions)
    conn.commit()
    cursor.execute(query_rebuild_specialties)
    conn.commit()
    cursor.execute(query_rebuild_locations)
    conn.commit()

    # Close the database connection
    cursor.close()
    conn.close()


def set_sql(state):
    # Establish a connection to the MySQL database
    conn = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='hellothere',
        database='sys'
    )
    cursor = conn.cursor()

    # clear tables
    query_rebuild_doctors = f"CREATE TABLE `doctors{'_' + state}` (`id` int NOT NULL AUTO_INCREMENT, `name` varchar(200) DEFAULT NULL, `city` varchar(45) DEFAULT NULL, `state` varchar(45) DEFAULT NULL, PRIMARY KEY (`id`), KEY `nameIdx` (`name`)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
    query_rebuild_conditions = f"CREATE TABLE `doctors_conditions{'_' + state}` (`id` int NOT NULL AUTO_INCREMENT, `doctor_name` varchar(200) DEFAULT NULL, `condition_treated` varchar(200) DEFAULT NULL, PRIMARY KEY (`id`), KEY `doctorName_idx` (`doctor_name`), CONSTRAINT `doctorNameConditions{'_' + state}` FOREIGN KEY (`doctor_name`) REFERENCES `doctors` (`name`)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
    query_rebuild_specialties = f"CREATE TABLE `doctors_specialties{'_' + state}` (`id` int NOT NULL AUTO_INCREMENT, `doctor_name` varchar(200) DEFAULT NULL, `specialty` varchar(200) DEFAULT NULL, PRIMARY KEY (`id`), KEY `doctorName_idx` (`doctor_name`), CONSTRAINT `doctorNameSpecialties{'_' + state}` FOREIGN KEY (`doctor_name`) REFERENCES `doctors` (`name`)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
    query_rebuild_locations = f"CREATE TABLE `doctors_locations{'_' + state}` (`id` int NOT NULL AUTO_INCREMENT, `doctor_name` varchar(200) DEFAULT NULL, `location_name` varchar(200) DEFAULT NULL, `address` varchar(200) DEFAULT NULL, `phone` varchar(200) DEFAULT NULL, `website` varchar(200) DEFAULT NULL, PRIMARY KEY (`id`), KEY `doctorName_idx` (`doctor_name`), CONSTRAINT `doctorNameLocations{'_' + state}` FOREIGN KEY (`doctor_name`) REFERENCES `doctors` (`name`)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"

    cursor.execute(query_rebuild_doctors)
    conn.commit()
    cursor.execute(query_rebuild_conditions)
    conn.commit()
    cursor.execute(query_rebuild_specialties)
    conn.commit()
    cursor.execute(query_rebuild_locations)
    conn.commit()

    # Close the database connection
    cursor.close()
    conn.close()
