"""
Configuration for various world scenarios used in knowledge graph generation.
Each scenario includes parameters for the number of iterations, questions, people, entities,
a description of the world, and the output directory for generated instances.
"""

CONFIGS = [
    # Original Italian-American Family Restaurant
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "A large italian-american family originated from New Jersey. "
        "Few of the members in the family works in the "
        "family-owned Italian restaurant 'Pangorio'.",
        "output_base_dir": "instances",
    },
    # Medical Emergency Department
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "An emergency department at St. Mary's Hospital in Chicago. "
        "Doctors, nurses, and paramedics handle trauma cases using "
        "X-ray machines, defibrillators, and share patient charts.",
        "output_base_dir": "instances",
    },
    # Japanese High School
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "Sakura High School in Tokyo where teenage students participate in "
        "robotics club. They share tools, computers, robot parts, and "
        "prepare together for the national competition.",
        "output_base_dir": "instances",
    },
    # Rural Indian Village
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "A farming village in Rajasthan, India. Neighbors share a water well, "
        "tractor, harvest equipment, and livestock. They help each other "
        "during planting season and festivals.",
        "output_base_dir": "instances",
    },
    # Tech Startup Office
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "A Silicon Valley AI startup. Engineers share cloud servers, "
        "development workstations, code repositories, API keys, and "
        "collaborate on machine learning models.",
        "output_base_dir": "instances",
    },
    # Arctic Research Station
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "A climate research station in Alaska. Scientists share ice core drills, "
        "weather monitoring equipment, snowmobiles, satellite phones, and "
        "collaborate on permafrost studies.",
        "output_base_dir": "instances",
    },
    # Brazilian Favela Community
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "A community in a Rio favela. Neighbors share electrical connections, "
        "water access, tools, and use the community center. They organize "
        "soccer matches and help with childcare.",
        "output_base_dir": "instances",
    },
    # Space Station Crew
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "International Space Station crew conducting experiments. Astronauts share "
        "life support systems, exercise equipment, research modules, food supplies, "
        "and maintain solar panels together.",
        "output_base_dir": "instances",
    },
    # Submarine Crew
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "A submarine crew on patrol in the Pacific. Sailors operate sonar systems, "
        "navigation equipment, share living quarters, mess facilities, and "
        "maintain the nuclear reactor.",
        "output_base_dir": "instances",
    },
    # African Safari Lodge
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "A wildlife lodge in Kenya's Maasai Mara. Guides, researchers, and staff "
        "share safari vehicles, radio equipment, binoculars, first aid kits, "
        "and coordinate wildlife tracking.",
        "output_base_dir": "instances",
    },
    # University Research Lab
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "A biochemistry lab at MIT studying gene editing. Graduate students share "
        "DNA sequencers, microscopes, centrifuges, chemical reagents, and "
        "collaborate on research papers.",
        "output_base_dir": "instances",
    },
    # Remote Australian Cattle Station
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "A cattle station in the Australian Outback. The family uses helicopters, "
        "water pumps, satellite phones, veterinary supplies, and coordinates "
        "cattle mustering across vast distances.",
        "output_base_dir": "instances",
    },
    # London Underground Maintenance Crew
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "Night shift maintenance crew for London's Tube system. Workers share "
        "specialized rail equipment, safety gear, diagnostic tools, and coordinate "
        "repairs across multiple stations.",
        "output_base_dir": "instances",
    },
    # Norwegian Fishing Vessel
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "A commercial fishing vessel in the North Sea. The crew shares fishing nets, "
        "sonar equipment, freezer storage, navigation systems, and works together "
        "processing the daily catch.",
        "output_base_dir": "instances",
    },
    # Tibetan Monastery
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "A Buddhist monastery in the Himalayas. Monks share meditation halls, "
        "sacred texts, kitchen facilities, prayer wheels, and maintain "
        "ancient manuscripts together.",
        "output_base_dir": "instances",
    },
    # New York Food Truck Collective
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "Food truck owners in Manhattan who share a commissary kitchen. They exchange "
        "cooking equipment, parking spots, supplier contacts, and coordinate "
        "at food festivals and events.",
        "output_base_dir": "instances",
    },
    # International Archaeological Dig
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "An archaeological team excavating Roman ruins in Turkey. Researchers share "
        "excavation tools, GPS equipment, artifact catalogs, camping gear, "
        "and collaborate on site documentation.",
        "output_base_dir": "instances",
    },
    # Mountain Rescue Team
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "A volunteer mountain rescue team in the Swiss Alps. Members share climbing "
        "equipment, medical supplies, avalanche beacons, helicopters, and "
        "coordinate emergency responses.",
        "output_base_dir": "instances",
    },
    # Comic Book Store Gaming Community
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "Regular customers at 'Heroes & Dice' comic store in Portland. They share "
        "board games, D&D books, miniature paints, dice sets, and organize "
        "weekly tournament nights.",
        "output_base_dir": "instances",
    },
    # Antarctic Weather Station
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "A remote weather monitoring station in Antarctica. The team shares "
        "weather balloons, satellite equipment, generators, food supplies, "
        "and maintains critical data collection systems.",
        "output_base_dir": "instances",
    },
    # Mexican Artisan Cooperative
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "Pottery artisans in Oaxaca, Mexico forming a cooperative. They share "
        "a kiln, clay supplies, glazes, workshop space, and sell their "
        "crafts together at markets.",
        "output_base_dir": "instances",
    },
    # Dubai Construction Site
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "A skyscraper construction site in Dubai. Engineers and workers share "
        "cranes, safety equipment, blueprints, concrete mixers, and coordinate "
        "complex building schedules.",
        "output_base_dir": "instances",
    },
    # Welsh Sheep Farm
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "A family sheep farm in rural Wales. They use herding dogs, shearing "
        "equipment, tractors, veterinary supplies, and work with neighbors "
        "during lambing season.",
        "output_base_dir": "instances",
    },
    # Singapore Hawker Center
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "Food stall owners at Maxwell Hawker Centre. Vendors share refrigeration, "
        "cooking gas connections, cleaning supplies, and help each other "
        "during busy lunch rushes.",
        "output_base_dir": "instances",
    },
    # Canadian Ranger Patrol
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 10,
        "num_people": 5,
        "num_entities": 5,
        "world_description": "Canadian Rangers patrolling the Arctic territories. They share snowmobiles, "
        "GPS devices, emergency shelters, communication radios, and coordinate "
        "search and rescue operations.",
        "output_base_dir": "instances",
    },
]
