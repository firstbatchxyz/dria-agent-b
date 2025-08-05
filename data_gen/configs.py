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
        {
    "num_iter_per_graph": 4,
    "num_qa_per_iter": 24,
    "num_people": 8,
    "num_entities": 20,
    "world_description": "Independent financial planner Jennifer serves middle-class families "
    "with budgeting, college savings, mortgage refinancing, and retirement planning. "
    "She maintains client financial profiles, investment tracking spreadsheets, "
    "educational resources, and works with loan officers and insurance brokers.",
    "output_base_dir": "instances",
    },
    {
        "num_iter_per_graph": 5,
        "num_qa_per_iter": 30,
        "num_people": 12,
        "num_entities": 25,
        "world_description": "Financial advisor Rachel manages portfolios for high-net-worth clients. "
        "She tracks investment accounts, retirement plans, insurance policies, "
        "tax documents, market research reports, and coordinates with CPAs, "
        "estate attorneys, insurance agents, and bank representatives.",
        "output_base_dir": "instances",
    },
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 16,
        "num_entities": 25,
        "num_people": 3,
        "world_description": "Bob's Hardware where the cashier tracks nuts, bolts, tools, paint supplies, "
        "gardening equipment, and seasonal items. They use inventory tracking systems, "
        "reorder point lists, supplier catalogs, and work with the owner "
        "and part-time helpers during busy seasons.",
        "output_base_dir": "instances",
    },
    {
        "num_iter_per_graph": 4,
        "num_qa_per_iter": 18,
        "num_people": 4,
        "num_entities": 20,
        "world_description": "Fresh Market grocery store where cashier Amy manages inventory using "
        "barcode scanners, price checkers, stock level sheets, vendor delivery schedules, "
        "and coordinates with store manager, stockers, and delivery drivers "
        "for restocking produce, dairy, and packaged goods.",
        "output_base_dir": "instances",
    },
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 14,
        "num_people": 5,
        "num_entities": 10,
        "world_description": "An accounting firm where Lisa, who is blind, works as a financial analyst. "
        "She uses JAWS software, Braille printers, accessible keyboards, "
        "audio conference systems, and collaborates with colleagues who provide "
        "visual document descriptions and meeting notes.",
        "output_base_dir": "instances",
    },
    {
        "num_iter_per_graph": 4,
        "num_qa_per_iter": 16,
        "num_people": 4,
        "num_entities": 12,
        "world_description": "Marcus, who is blind, navigates daily life using screen readers, "
        "Braille displays, voice assistants, GPS navigation apps, and tactile markers. "
        "He coordinates with his guide dog trainer, mobility instructor, "
        "and family members for shopping and appointments.",
        "output_base_dir": "instances",
    },
    {
        "num_iter_per_graph": 4,
        "num_qa_per_iter": 22,
        "num_people": 7,
        "num_entities": 18,
        "world_description": "ServerCloud enterprise support handling multi-tenant deployments, "
        "load balancers, container orchestration, and monitoring systems. "
        "DevOps specialists share runbooks, incident response procedures, "
        "client configurations, and coordinate with network engineers.",
        "output_base_dir": "instances",
    },
    {
        "num_iter_per_graph": 5,
        "num_qa_per_iter": 25,
        "num_people": 8,
        "num_entities": 15,
        "world_description": "CloudCRM enterprise support team serving Fortune 500 clients. "
        "Support engineers handle API integrations, database migrations, custom workflows, "
        "security configurations, and share escalation procedures, knowledge bases, "
        "client environment details, and SLA tracking systems.",
        "output_base_dir": "instances",
    },
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 18,
        "num_people": 5,
        "num_entities": 12,
        "world_description": "AutoParts Plus customer service team handling brake systems, engine components, "
        "and electrical parts. Representatives use parts catalogs, compatibility databases, "
        "installation videos, return authorization forms, and work with mechanics "
        "and DIY customers.",
        "output_base_dir": "instances",
    },
    {
        "num_iter_per_graph": 4,
        "num_qa_per_iter": 20,
        "num_people": 6,
        "num_entities": 10,
        "world_description": "TechHome customer support center for smart kitchen appliances. "
        "Support agents handle warranty claims, troubleshooting guides, replacement parts, "
        "installation manuals, customer complaint tickets, and coordinate with "
        "field technicians and product engineers.",
        "output_base_dir": "instances",
    },
    {
        "num_iter_per_graph": 3,
        "num_qa_per_iter": 12,
        "num_people": 4,
        "num_entities": 6,
        "world_description": "Sunnydale Memory Care facility where residents with advanced dementia "
        "share common areas, activity schedules, meal routines, and personal belongings. "
        "Nurses, family members, and therapists help maintain daily structure and "
        "familiar routines for cognitive support.",
        "output_base_dir": "instances",
    },
    {
        "num_iter_per_graph": 4,
        "num_qa_per_iter": 15,
        "num_people": 3,
        "num_entities": 8,
        "world_description": "Eleanor, 78, lives in her own apartment with early-stage Alzheimer's. "
        "She uses daily reminder systems, medication organizers, family photo albums, "
        "calendar with appointments, emergency contact lists, and receives visits from "
        "her daughter Sarah and home care aide Maria.",
        "output_base_dir": "instances",
    }
]
