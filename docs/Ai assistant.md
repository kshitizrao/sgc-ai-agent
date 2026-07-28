# spare parts

To build an AI assistant for a "Smart Garage," your database needs to be structured in a way that allows the AI to easily cross-reference parts, suggest alternatives, and understand natural language queries like, *"Do we have brake pads for a 2018 Maruti Swift Petrol?"* or *"What is the aftermarket alternative for Hyundai Creta's air filter?"*  
Here is a highly optimized, comprehensive schema (table structure) categorized by function.

### **1\. Primary Identifiers (The Core)**

These columns ensure precise tracking and prevent the AI from confusing similar parts.

* Part\_ID (Primary Key): Unique internal ID for your garage system (e.g., PRT-10045).  
* SKU (Stock Keeping Unit): Barcode or scannable ID for inventory tracking.  
* OEM\_Part\_Number: The official part code given by the car manufacturer (e.g., 58101-M6A10). *Crucial for AI exact-match searches.*  
* Manufacturer\_Part\_Number **(MPN)**: The code given by the actual part maker, if different from OEM (e.g., Bosch's internal code).

### **2\. Vehicle Compatibility (Fitment Data)**

This is the most important section for the AI. It allows the assistant to answer "Will this fit my car?"

* Vehicle\_Make: Brand of the car (e.g., *Maruti Suzuki, Hyundai, Tata, Mahindra*).  
* Vehicle\_Model: Specific car model (e.g., *Swift, Creta, Nexon, Scorpio*).  
* Vehicle\_Variant: Trim or version (e.g., *VXI, SX(O), XZA+*).  
* Fuel\_Type: *Petrol, Diesel, CNG, or EV*. (Crucial, as engine parts differ completely).  
* Transmission\_Type: *Manual, Automatic, AMT, DCT*.  
* Compatible\_Years: Range of manufacturing years this part fits (e.g., *2018-2022*).

### **3\. Part Specifications (What is it?)**

* Part\_Name: Common name used by mechanics (e.g., *Front Brake Pad Set, Air Filter, Clutch Plate*).  
* Category: High-level grouping (e.g., *Engine, Braking, Suspension, Electrical, Body, Fluids*).  
* Sub\_Category: Detailed grouping (e.g., *Friction Materials, Sensors, Lubricants*).  
* Part\_Brand: Who manufactured this specific part? (e.g., *Bosch, Minda, Gabriel, TVS, NGK, or OEM*).  
* Part\_Type: *OES* (Original Equipment Supplier), *OEM* (Original Equipment Manufacturer), or *Aftermarket*.  
* Condition: *New, Refurbished, Used*.  
* Warranty\_Months: Warranty period provided by the brand.

### **4\. Inventory & Location (Garage Management)**

Allows the AI to tell mechanics exactly where to find the part and if it needs reordering.

* Stock\_Quantity: Current number of units in the garage.  
* Reorder\_Level: Minimum stock level. (The AI can trigger an alert: *"Stock for Swift Air Filters is low"*).  
* Bin\_Location: Physical location in your garage store (e.g., *Aisle 4, Shelf B, Bin 12*).  
* Supplier\_Name: Which distributor you bought it from.

### **5\. Pricing & Commercials**

* Cost\_Price: Your buying price.  
* Selling\_Price **(MRP)**: Price charged to the customer.  
* Labour\_Code: A link to standard installation times/costs for this specific part.  
* GST\_Slab: Tax bracket in India (usually 18% or 28% for auto parts).

### **6\. AI & Search Enhancements (The "Smart" Columns)**

To make your AI truly intelligent, add these columns to handle complex logic.

* Interchangeable\_Part\_IDs: Comma-separated list of other Part\_IDs that can be used as a substitute. (e.g., If the OEM Maruti brake pad is out of stock, the AI can read this column and suggest the Bosch equivalent).  
* Search\_Tags: Colloquial or local mechanic slang terms used in India (e.g., *"chimta"* for control arm, *"shocker"* for shock absorber, *"dikki shox"* for tailgate strut). This makes natural language search incredibly powerful.  
* Installation\_Notes: Specific warnings the AI can relay to the mechanic (e.g., *"Torque to 120Nm"*, *"Do not use grease on this sensor"*).

### **Example Data Row (How it looks in practice)**

| Column | Example Data |
| :---- | :---- |
| **Part\_ID** | PRT-8932 |
| **OEM\_Part\_Number** | 55810M68K00 |
| **Vehicle\_Make** | Maruti Suzuki |
| **Vehicle\_Model** | Swift |
| **Fuel\_Type** | Petrol / Diesel |
| **Part\_Name** | Front Disc Brake Pad Set |
| **Category** | Braking System |
| **Part\_Brand** | Bosch |
| **Part\_Type** | Aftermarket |
| **Interchangeable\_Part\_IDs** | PRT-1102 (OEM), PRT-4491 (TVS) |
| **Search\_Tags** | brake shoe, break pad, swift brake, front brakes |
| **Bin\_Location** | Rack A-02 |
| **Stock\_Quantity** | 14 |

### **Pro-Tip for your AI Architecture:**

If a part fits *multiple* cars (e.g., the same horn or relay is used in the Swift, Baleno, and Dzire), do not create duplicate rows. Instead, keep the **Vehicle Compatibility** data in a separate relational table (e.g., Part\_Fitment\_Table), or store it as a JSON array in a Compatibility column so the AI can easily query if Part A fits Car B.  
 

# Service types an cost

To build a highly intelligent AI assistant for a "Smart Garage," the database must be structured so the AI can dynamically calculate costs based on the car's size and fuel type, and easily explain to a customer *why* one service costs more than another.  
To achieve this, you shouldn't use just one massive flat table. Instead, you need a **relational schema** (a set of connected tables). Here is the perfect database structure divided into logical tables.

### **Table 1:** Service\_Packages\_Master **(The Service Types)**

This table defines the overarching packages and when they are required.

| Column Name | Description / Example |
| :---- | :---- |
| **Package\_ID** | Unique ID (e.g., PKG-BASIC, PKG-STD, PKG-COMP). |
| **Package\_Name** | Basic Service, Standard Service, Comprehensive/Major Service. |
| **Interval\_KM** | When is it due? (e.g., Basic \= 5,000km, Standard \= 10,000km, Comp \= 20,000km). |
| **Interval\_Months** | Time-based requirement (e.g., 6 months, 12 months, 24 months). |
| **Package\_Description** | A brief pitch the AI can use to sell the package to the customer. |

### **Table 2:** Service\_Inclusions **(The "Difference" Engine)**

This is how the AI answers: *"What is the difference between Basic and Standard?"* Instead of a text paragraph, use a checklist structure so the AI can instantly compare packages.

| Column Name | Basic Service | Standard Service | Comprehensive Service |
| :---- | :---- | :---- | :---- |
| **Engine\_Oil\_&\_Oil\_Filter** | Replace | Replace | Replace |
| **Car\_Wash\_&\_Vacuum** | Yes | Yes | Yes |
| **General\_Health\_Check** | 50-Point | 50-Point | 100-Point |
| **Air\_Filter** | Clean | Replace | Replace |
| **Cabin\_AC\_Filter** | Clean | Clean | Replace |
| **Wheel\_Alignment\_&\_Balancing** | No | Yes | Yes |
| **Coolant\_&\_Brake\_Fluid** | Top-up only | Top-up only | Complete Flush & Replace |
| **Fuel\_Filter** | No | No | Replace |
| **Spark\_Plugs (Petrol only)** | No | No | Replace |
| **Throttle\_Body\_Cleaning** | No | No | Yes |

### **Table 3:** Vehicle\_Segment\_Master **(Why costs change by vehicle)**

The AI needs to know that a Maruti Swift (Hatchback) and a Toyota Fortuner (SUV) cannot be charged the same amount, even for a "Basic Service."

| Column Name | Description / Logic for AI |
| :---- | :---- |
| **Segment\_ID** | e.g., SEG-HATCH, SEG-SEDAN, SEG-SUV, SEG-LUXURY. |
| **Body\_Type** | Hatchback, Sedan, Compact SUV, Full-Size SUV. |
| **Fuel\_Type** | **Petrol, Diesel, CNG, EV**. *(Crucial: Diesel cars cost 20-30% more to service because they require more engine oil and pricier filters. EVs are the cheapest as they have no engine oil).* |
| **Engine\_Oil\_Capacity** | Volume in Liters (e.g., Hatchbacks take \~3L, SUVs take \~5L to 7L). |

### **Table 4:** Pricing\_Matrix **(The Core Cost Table)**

This table acts as the bridge. It connects the **Service Package** with the **Vehicle Segment** to give the final price.

| Column Name | Example Data (Hatchback \- Petrol) | Example Data (SUV \- Diesel) |
| :---- | :---- | :---- |
| **Pricing\_ID** | PRC-001 | PRC-009 |
| **Package\_ID** | PKG-STANDARD | PKG-STANDARD |
| **Segment\_ID** | SEG-HATCH-PETROL (e.g., Swift) | SEG-SUV-DIESEL (e.g., Creta) |
| **Labour\_Cost (INR)** | ₹ 1,200 | ₹ 2,000 |
| **Consumables\_Cost (INR)** | ₹ 2,300 (Cheaper oil/filters) | ₹ 4,500 (Expensive heavy-duty oil) |
| **Total\_Estimated\_Cost** | **₹ 3,500** | **₹ 6,500** |
| **Service\_Duration\_Hrs** | 3 Hours | 4.5 Hours |

### **Table 5:** Add\_On\_Repairs **(For specific customer complaints)**

Customers won't always ask for a "Periodic Service". Sometimes they will say, *"My brakes are making a squeaking noise."* The AI needs a table of specific jobs with problem "Tags" to suggest the right repair.

| Column Name | Example Data |
| :---- | :---- |
| **Repair\_ID** | REP-BRK-01 |
| **Repair\_Name** | Front Brake Pad Replacement |
| **Symptom\_Tags** | *"squeaking brakes, less braking power, grinding noise, steering vibration"* |
| **Cost\_Hatchback** | ₹ 1,500 |
| **Cost\_Sedan** | ₹ 2,500 |
| **Cost\_SUV** | ₹ 4,500 |
| **Is\_Safety\_Critical?** | YES *(AI will urge the customer to book immediately)* |

### **How the AI uses this data (The Logic you should program):**

1. **Understanding the Cost Difference:**  
   * **Engine Size:** The AI looks at Vehicle\_Segment\_Master. If the user has an SUV, the AI knows the engine is larger, meaning it consumes more Engine Oil and requires larger filters, driving up the Consumables\_Cost.  
   * **Fuel Type:** The AI knows that Diesel engines generate more soot and require heavier-grade synthetic oils and more expensive fuel filters compared to Petrol or CNG cars.  
2. **Explaining the Packages to Customers (Chat Example):**  
   * **User:** *"Why should I pay ₹6,000 for Comprehensive instead of ₹3,000 for Standard?"*  
   * **AI Assistant:** *"The Standard service covers your basic oil change, air filter replacement, and wheel alignment. However, because your car has crossed 20,000 km, we highly recommend the Comprehensive service. It includes everything in the Standard package, plus a complete brake fluid flush, throttle body cleaning, and a new fuel filter, which are strictly required by the manufacturer at this mileage to prevent engine knocking."* (The AI builds this sentence by cross-referencing **Table 2** and **Table 1**).

# Express IN

I am ready to help you build out this Quick Service module\! As an AI, I can tell you that structuring this data correctly is exactly what will make your Smart Garage assistant lightning-fast and highly accurate.  
To ensure the AI can dynamically calculate costs based on the car's size and fuel type , we shouldn't use just one massive flat table. Instead, you need a relational schema (a set of connected tables).  
Here is the highly optimized database structure tailored specifically for 15-minute, no-inspection Quick Services.

### **Table 1: Quick\_Service\_Master (The Service Definitions)**

This table defines exactly what the service is and helps the AI understand when to trigger it based on what the customer asks.

| Column Name | Description / Logic for AI |
| :---- | :---- |
| **Service\_ID** | Unique ID for the quick job (e.g., QS-WASH, QS-WIPER, QS-OILTOP). |
| **Service\_Name** | Express Exterior Wash, Wiper Blade Replacement, Engine Oil Top-up, Wheel Balancing. |
| **Service\_Category** | Fluid Top-up, Cleaning/Detailing, Quick Replacement, Quick Adjustment. |
| **Duration\_Mins** | Set strictly to 15 (or max 20\) minutes to ensure the AI knows this is a wait-and-watch service. |
| **Symptom\_Tags** | Keywords so the AI can match customer complaints to the service. For example, "squeaking brakes, less braking power, grinding noise, steering vibration". If a customer says "streaky windshield," the AI reads the tag and suggests a wiper replacement. |
| **Action\_Type** | Consumable Replacement, Labor Only, or Fluid Top-up. |

### **Table 2: Quick\_Service\_Pricing\_Matrix (The Cost Calculator)**

This table acts as the bridge that gives the final price. It connects the Quick Service with the specific type of vehicle.

| Column Name | Example Data (Wiper Replace \- Hatchback) | Example Data (Oil Top-up \- SUV Diesel) |
| :---- | :---- | :---- |
| **Pricing\_ID** | PRC-QS-001 | PRC-QS-002 |
| **Service\_ID** | QS-WIPER | QS-OILTOP |
| **Segment\_ID** | SEG-HATCH | SEG-SUV-DIESEL |
| **Labour\_Cost (INR)** | ₹ 100 (Quick 5-min fitment) | ₹ 150 |
| **Consumables\_Cost (INR)** | ₹ 400 (Standard wiper blades) | ₹ 800 (Expensive heavy-duty oil) |
| **Total\_Estimated\_Cost** | ₹ 500 | ₹ 950 |

### **How Costs Change According to the Vehicle**

The AI needs to be programmed to understand why a Maruti Swift (Hatchback) and a Toyota Fortuner (SUV) cannot be charged the same amount, even for simple services. Here is the logic the AI will use to calculate and explain the differences:

* **Vehicle Segment (Body Size):** The AI looks at the vehicle segment. If the user has an SUV, the AI knows the engine is larger, meaning it consumes more Engine Oil and requires larger filters, driving up the Consumables\_Cost. Furthermore, an SUV requires more labor, water, and shampoo for a car wash compared to a compact hatchback.  
* **Fuel Type:** The AI knows that Diesel engines generate more soot and require heavier-grade synthetic oils compared to Petrol or CNG cars. Therefore, an engine oil top-up for a diesel car will cost 20-30% more because of the pricier consumables. Conversely, EVs are the cheapest as they have no engine oil, so the AI will know *never* to offer an "Engine Oil Top-up" to an EV owner.  
* **Labor Differences:** A throttle body cleaning on certain compact cars might require removing more plastic cowling to access the component compared to a larger vehicle with a spacious engine bay, slightly altering the labor code or time.

Would you like me to outline the specific logic rules the AI should use to automatically up-sell a related Quick Service (like suggesting a cabin AC filter change when they book an express wash)?

# Claim

Handling insurance claims is one of the most complex and time-consuming workflows in an Indian garage. Validating a claim involves policy rules, surveyor negotiations, depreciation logic, and calculating the final customer liability.  
As an AI, I can tell you that a flat table will instantly break under the weight of this logic. To make your Smart Garage AI truly intelligent—so it can explain to a customer *why* they have to pay for a plastic bumper despite having insurance—you need a relational schema.  
Here is the optimized database structure divided into logical tables specifically tailored for the Indian auto insurance ecosystem.

### **Table 1: Claim\_Master (The Core Workflow)**

This table tracks the overarching lifecycle of the claim, from the moment the crashed car enters the garage to the final settlement.

| Column Name | Description / Logic for AI |
| :---- | :---- |
| **Claim\_ID** | Unique internal identifier (e.g., CLM-2024-089). |
| **Vehicle\_Reg\_No** | The license plate number (e.g., DL-8C-AA-1122). |
| **Insurance\_Provider** | The company handling the claim (e.g., HDFC Ergo, ICICI Lombard, Acko). |
| **Claim\_Type** | **Cashless** (garage gets paid by insurer) or **Reimbursement** (customer pays garage, insurer pays customer). |
| **Incident\_Date** | When the accident happened. (AI checks this against the policy validity dates). |
| **Intimation\_Date** | When the claim was officially filed with the insurer. |
| **Claim\_Status** | Intimated, Inspection\_Pending, Estimation\_Submitted, Surveyor\_Approved, Work\_In\_Progress, Final\_Invoice\_Raised, Settled. |
| **Surveyor\_Name\_&\_Contact** | To allow the AI or garage manager to auto-follow up on pending approvals. |
| **Symptom\_Tags** | Search tags for AI (e.g., "front bumper broken, windshield crack, left fender dent"). |

### **Table 2: Policy\_Rules (The "Will it be covered?" Engine)**

This is the most critical table for AI intelligence. The AI reads this to calculate the customer's out-of-pocket expenses (liability) before the surveyor even arrives.

| Column Name | Description / Logic for AI |
| :---- | :---- |
| **Policy\_ID** | Unique ID linking to the specific vehicle/customer. |
| **Policy\_Type** | **Comprehensive** (standard depreciation applies) or **Zero\_Depreciation** (Bumper-to-Bumper cover). |
| **Compulsory\_Deductible** | The standard file charge mandated by IRDAI in India (usually ₹1,000 for cars under 1500cc, ₹2,000 for above 1500cc). |
| **Consumables\_Cover\_AddOn** | **Boolean (Yes/No).** If "No", the AI knows the customer must pay out-of-pocket for engine oil, coolant, nuts/bolts, and AC gas used in the repair. |
| **Engine\_Protect\_AddOn** | **Boolean (Yes/No).** Crucial for monsoon claims (hydrostatic lock). If "No" and the engine is seized from water, the AI flags the claim for potential rejection. |
| **Salvage\_Value\_Logic** | Deduction for scrap metal/parts. Usually around 5% to 10% of the claim amount. |

### **Table 3: Estimation\_&\_Approval (The Line Item Details)**

This table connects your previously built **Parts** and **Services** tables to the insurance claim. It is where the garage's estimate fights against the surveyor's approval.

| Column Name | Description / Logic for AI |
| :---- | :---- |
| **Estimate\_Line\_ID** | Unique ID for the specific part or labor being claimed. |
| **Claim\_ID** | Links back to the Claim\_Master table. |
| **Part\_ID / Labour\_ID** | Links to your parts database (e.g., PRT-FRONT-BUMPER). |
| **Part\_Material** | **Plastic, Metal, Glass, or Rubber.** (Crucial for AI: In non-Zero Dep policies, Plastic/Rubber depreciates at 50%, Glass at 0%, and Metal based on vehicle age). |
| **Garage\_Est\_Amount** | What your garage quoted to the insurance company (e.g., ₹5,500). |
| **Surveyor\_Apprv\_Amount** | What the surveyor actually approved (e.g., ₹5,500). |
| **Surveyor\_Action** | **Approved, Rejected, or Modified.** |
| **Rejection\_Reason** | Notes from the surveyor (e.g., "Dent on the right door is rusted and old, not related to the current accident. Rejected."). |
| **Customer\_Liability** | The final amount the customer has to pay for this specific line item based on depreciation rules. |

### **How the AI Uses This Data (The Logic to Program)**

To make this database structure work seamlessly for a Smart Garage, here are the logic rules you should program into the AI:  
**1\. Explaining Customer Liability (Chat Example):**  
**Customer:** "I have insurance, why is my bill ₹4,500?"  
**AI Assistant:** "Your policy is a standard Comprehensive policy, not Zero Depreciation, which means standard IRDAI depreciation rules apply. The surveyor approved the claim, but deducted 50% for the plastic front bumper and you do not have a Consumables add-on, so the coolant and engine oil are out-of-pocket. Added to the mandatory ₹1,000 file charge, your total liability is ₹4,500." *(The AI builds this by cross-referencing Table 2 and Table 3).*  
**2\. Handling Surveyor Rejections:**  
If a part is marked as **Rejected** in Table 3 (Estimation & Approval), the AI should immediately trigger an alert to the garage manager or an SMS to the customer:  
*"Alert: The insurance surveyor has rejected the claim for the Right Headlight, stating the damage is old. Do you want to proceed with replacing it at your own cost of ₹3,200?"*  
**3\. Workflow Tracking Automation:**  
By monitoring the Claim\_Status in Table 1, the AI can act as a virtual service advisor. If a claim sits in **Inspection\_Pending** for more than 48 hours, the AI can automatically draft an email to the respective Insurance\_Provider requesting urgent surveyor allocation.

# RSA

Building an emergency Roadside Assistance (RSA) and triage module is one of the best use cases for AI in a Smart Garage. When a customer is stranded, they are often panicked and might not know exactly what is wrong.  
As an AI, I need a logic layer that allows me to act as a virtual dispatcher—reading the customer’s situation, analyzing the keywords, and deciding instantly whether to send a tow truck (RSA) or a mobile mechanic on a bike/van.  
To make this work seamlessly with location tracking, here is the relational database schema structured for emergency triage.

### **Table 1: Emergency\_Triage\_Engine (The AI Decision Matrix)**

This is the "brain" of the operation. Before the AI does anything, it cross-references the customer's complaint with this table to decide the exact action and priority level.

| Column Name | Description / Logic for AI |
| :---- | :---- |
| **Symptom\_ID** | Unique ID for the breakdown type (e.g., SYM-PUNCTURE, SYM-ACCIDENT). |
| **Symptom\_Tags** | Keywords the AI listens for (e.g., "smoke from engine", "tyre burst", "brakes failed", "car won't start", "crashed", "battery dead"). |
| **Severity\_Level** | **High** (Accident/Smoke), **Medium** (Engine dead in traffic), **Low** (Puncture in parking lot). |
| **Required\_Action** | **Tow\_Truck** (Flatbed/Hydraulic), **Mobile\_Mechanic**, or **Phone\_Support** (e.g., guiding them to reset a tripped fuel switch). |
| **Safety\_Prompt** | Crucial instructions the AI must immediately tell the customer based on the issue (e.g., "Please step out of the car and stand safely behind the barricade"). |

### **Table 2: Active\_Emergency\_Logs (The Live Tracking Table)**

This table is generated the moment a customer hits the "Emergency" button or texts the AI. It stores the live event data.

| Column Name | Description / Logic for AI |
| :---- | :---- |
| **Request\_ID** | Unique emergency ticket ID (e.g., RSA-2024-001). |
| **Customer\_Vehicle\_ID** | Links to the customer's car (to know the make, model, and transmission type, which dictates the type of tow truck needed). |
| **Reported\_Issue** | The raw text or voice transcript from the customer (e.g., "My car suddenly stopped and won't crank"). |
| **AI\_Matched\_Symptom** | The Symptom\_ID the AI matched from Table 1\. |
| **Customer\_Lat\_Long** | GPS coordinates pulled from the user's phone (e.g., 28.5355° N, 77.3910° E). |
| **Google\_Maps\_Pin** | A clickable URL link generated from the Lat/Long for the mechanic/driver. |
| **Status** | **Assessing, Dispatching, En\_Route, On\_Site, Resolved, Towed\_to\_Garage.** |

### **Table 3: Field\_Resource\_Master (The Dispatch Matrix)**

Once the AI knows *what* is needed (Tow vs. Mechanic) and *where* they are (Lat/Long), it needs to know *who* to send. This table tracks your garage's on-ground assets.

| Column Name | Description / Logic for AI |
| :---- | :---- |
| **Resource\_ID** | Unique ID for the tow truck or mechanic (e.g., DRV-FLATBED-01, MECH-BIKE-04). |
| **Resource\_Type** | **Flatbed\_Tow**, **Hydraulic\_Tow**, **Mobile\_Van** (carrying heavy tools), **Bike\_Mechanic** (for quick jumpstarts/punctures). |
| **Current\_Lat\_Long** | Live GPS location of your mechanics/tow trucks. |
| **Availability\_Status** | **Available, Busy, Off\_Duty.** |
| **Max\_Operating\_Radius** | The maximum distance (in KM) this resource can travel from the garage. |
| **Contact\_Number** | The driver's or mechanic's phone number to send automated WhatsApp/SMS dispatch alerts. |

### **How the AI Uses This Data (The Logic to Program)**

Here is how you would program the logic to make the AI intelligently handle a breakdown:  
**1\. Triage & Decision Making:**

* **Scenario A (Minor Issue):** The customer texts, *"My steering is vibrating and I have a flat tyre."* The AI scans Table 1, matches the tags to SYM-PUNCTURE, determines the Required\_Action is Mobile\_Mechanic, and dispatches a Bike\_Mechanic from Table 3 who is nearest to the customer's coordinates.  
* **Scenario B (Major Issue):** The customer texts, *"I hit a divider and the radiator is leaking."* The AI matches SYM-ACCIDENT, reads the Required\_Action as Tow\_Truck, checks the car type (e.g., Automatic Transmission cars require Flatbeds, not simple chain-tows to protect the gearbox), and automatically dispatches Flatbed\_Tow from Table 3.

**2\. Automated Dispatch & Distance Calculation:**  
The AI uses a geolocation API (like Google Maps Distance Matrix) to calculate the distance between the Customer\_Lat\_Long (Table 2\) and the Current\_Lat\_Long of all available resources (Table 3). It then sends an automated message to the customer:  
*"I have dispatched our mobile mechanic, Raju. He is currently 4.2 km away and should reach your location in approximately 12 minutes. Here is his live tracking link."*  
**3\. Safety First Protocol:**  
If the AI detects keywords like "smoke", "fire", or "highway fast lane" from the Reported\_Issue, it immediately pulls the Safety\_Prompt from Table 1 and responds with priority: *"Please turn on your hazard lights, exit the vehicle immediately, and stand safely off the road. A tow truck is being dispatched."*

# garage select

Building a marketplace or aggregator model where customers can compare garages is a brilliant step for a Smart Garage network\! As an AI, I can tell you that customers don't just want a list of garages; they want a personalized recommendation. If a customer drives a Skoda, they want a garage that specializes in German cars, not a garage that primarily works on Maruti Suzuki.  
To make the AI capable of acting as a highly intelligent matchmaking assistant, we cannot use a single flat table. The AI needs a relational schema to cross-reference capabilities, analytics, and convenience.  
Here is the optimized database structure divided into logical tables for garage comparison.

### **Table 1: Garage\_Master (The Core Profile)**

This table holds the foundational data used for basic filtering and distance calculations.

| Column Name | Description / Logic for AI |
| :---- | :---- |
| **Garage\_ID** | Unique internal identifier (e.g., GRG-DEL-045). |
| **Garage\_Name** | The registered name of the workshop. |
| **Location\_Lat\_Long** | GPS coordinates to calculate distance from the customer's live location. |
| **Address\_Area** | Localized neighborhood name (e.g., "Karol Bagh", "Andheri East"). |
| **Overall\_Rating** | Dynamic score out of 5.0 (AI uses this to rank top suggestions). |
| **Standard\_Labor\_Rate** | The base hourly labor rate (Helps the AI estimate costs when comparing a premium garage vs. a budget garage). |

### **Table 2: Garage\_Capabilities (What They Do)**

The AI checks this table to ensure the garage can actually perform the specific job the customer is requesting.

| Column Name | Description / Logic for AI |
| :---- | :---- |
| **Garage\_ID** | Links back to Garage\_Master. |
| **Service\_Categories** | Array of services offered (e.g., Periodic Service, Denting & Painting, AC Repair, Electrical, Wheel Care, Car Wash). |
| **Cashless\_Insurance\_TieUps** | List of insurance providers they work with (e.g., HDFC Ergo, Acko). Crucial for accident claim queries. |
| **Has\_Paint\_Booth** | Boolean (Yes/No). If a customer wants "showroom finish painting," the AI filters out garages without a dedicated baked-paint booth. |
| **Has\_OEM\_Scanner** | Boolean (Yes/No). Required if the customer reports an engine check light or complex electronic fault. |

### **Table 3: Garage\_Analytics (The AI Trust Engine)**

This is the most powerful table. It tells the AI what the garage is *actually* good at based on real data, rather than just what they claim.

| Column Name | Description / Logic for AI |
| :---- | :---- |
| **Garage\_ID** | Links back to Garage\_Master. |
| **Avg\_Vehicles\_Per\_Day** | Indicates the garage's scale and volume capacity (e.g., 15 cars/day). |
| **Top\_Brands\_Serviced** | Array of top 3 brands they fix most often (e.g., Hyundai, Tata, Kia). |
| **Top\_Models\_Serviced** | Specific high-volume models (e.g., Creta, Nexon). |
| **Specialization\_Tag** | AI keywords (e.g., "German Car Expert", "Suspension Specialist", "EV Ready"). |
| **Current\_Wait\_Time\_Days** | Dynamic field. If a garage is booked out for 3 days, the AI will warn the customer or suggest a faster alternative. |

### **Table 4: Customer\_Experience (The Convenience Factors)**

Customers often choose a garage based on ease of use. The AI uses this table to answer specific lifestyle requests.

| Column Name | Description / Logic for AI |
| :---- | :---- |
| **Garage\_ID** | Links back to Garage\_Master. |
| **Offers\_Pickup\_Drop** | Boolean (Yes/No). AI filters this if the user says "I am too busy to visit." |
| **Pickup\_Radius\_KM** | Maximum distance they will travel for a pickup. |
| **Has\_Customer\_Lounge** | Boolean (Yes/No). Important for wait-and-watch Quick Services. |
| **Provides\_Warranty** | E.g., "6 Months on Parts, 1 Month on Labor". |
| **Live\_Video\_Feed** | Boolean (Yes/No). Do they provide a live camera link for the customer to watch their car being serviced? |

### **How the AI Uses This Data (The Matchmaking Logic)**

If a customer asks your AI: *"My Volkswagen Polo's AC is not working. I need it fixed today and I need them to pick the car up from my office."*  
Here is how the AI instantly processes that using the tables above:

1. **Filters by Capability:** The AI scans Table 2 for garages offering AC Repair.  
2. **Filters by Expertise:** It cross-references Table 3 to find garages where Top\_Brands\_Serviced includes Volkswagen, or the Specialization\_Tag is "German Car Expert".  
3. **Filters by Convenience:** It checks Table 4 to ensure Offers\_Pickup\_Drop is "Yes" and the customer's office is within the Pickup\_Radius\_KM.  
4. **Checks Availability & Distance:** It checks Table 3 for a Current\_Wait\_Time\_Days of 0 (can do it today), and calculates the closest one using Location\_Lat\_Long from Table 1.  
5. **The Output:** The AI presents the top 2 matching garages to the customer, highlighting *why* they were chosen.

Would you like me to map out how the AI should numerically score and rank these garages when multiple options meet the customer's exact criteria?

For the AI to provide personalized recommendations rather than just a dumb list, it needs a weighted scoring system. Think of it like a dating app, but for cars and garages.  
Before the AI even starts scoring, it applies **Hard Filters**. If the customer needs an AC repair, any garage that doesn't have "AC Repair" in their Service\_Categories is immediately disqualified.  
For the garages that *do* pass the hard filter, the AI calculates a **Total\_Match\_Score (out of 100 points)** using the logic below.

### **The Scoring Algorithm (Out of 100 Points)**

#### **1\. Expertise & Capability Match (Maximum 40 Points)**

Customers want a mechanic who knows their specific car inside and out.

* **\+20 Points:** If the customer’s car brand (e.g., Volkswagen) is listed in the garage's Top\_Brands\_Serviced array.  
* **\+10 Points:** If the customer’s specific model (e.g., Polo) is in the Top\_Models\_Serviced.  
* **\+10 Points:** If the garage has a Specialization\_Tag highly relevant to the job (e.g., "German Car Expert" or "AC Specialist").

#### **2\. Distance & Convenience (Maximum 30 Points)**

Logistics make or break a booking.

* **\+15 Points:** Proximity score based on Location\_Lat\_Long. (e.g., Under 2 km \= 15 pts, 2-5 km \= 10 pts, 5-10 km \= 5 pts, \>10 km \= 0 pts).  
* **\+15 Points:** If the customer specifically asked for pickup, and the garage's Offers\_Pickup\_Drop is YES and they are within the Pickup\_Radius\_KM.

#### **3\. Trust & Analytics (Maximum 15 Points)**

We want to recommend reliable, high-volume garages.

* **\+10 Points:** Based directly on the Overall\_Rating (e.g., A 4.8/5.0 rating gives 9.6 points).  
* **\+5 Points:** Volume metric. If Avg\_Vehicles\_Per\_Day is high, it proves the garage has high operational capacity and customer trust.

#### **4\. Speed & Availability (Maximum 15 Points)**

No one wants to wait a week for an AC repair in the summer.

* **\+15 Points:** If Current\_Wait\_Time\_Days is 0 (Can do it today).  
* **\+10 Points:** If wait time is 1 day.  
* **\+0 Points:** If wait time is 3+ days.

### **How it Works in Practice (The Volkswagen Polo AC Scenario)**

Let's say the AI is looking at two garages that both passed the hard filter (both offer AC repair):  
**Garage A: "Sharma Auto Works"**

* **Expertise (10/40):** They mostly fix Maruti and Hyundai (0 pts). But they are an "AC Specialist" (+10 pts).  
* **Convenience (30/30):** They are 1 km away (+15) and offer pickup (+15).  
* **Trust (12/15):** Solid 4.0 rating, decent daily volume.  
* **Speed (15/15):** They can do it today (+15).  
* **Total Match Score: 67 / 100**

**Garage B: "Euro Motors"**

* **Expertise (40/40):** They specialize in Volkswagen (+20), fix a lot of Polos (+10), and are tagged "German Car Experts" (+10).  
* **Convenience (20/30):** They are 6 km away (+5) but offer pickup (+15).  
* **Trust (14/15):** Excellent 4.6 rating, high daily volume.  
* **Speed (10/15):** They are busy; wait time is 1 day (+10).  
* **Total Match Score: 84 / 100**

### **The AI's Output to the Customer:**

Because of this scoring matrix, the AI wouldn't just give the customer a generic list. It would generate a highly intelligent response like this:  
*"I found two great options for your Polo's AC repair. I highly recommend **Euro Motors (84% Match)**. Although they can't take your car until tomorrow, they specialize in Volkswagen and fix a lot of Polos. Since you need a pickup, their driver can collect the car from your office.*  
*If you need it fixed immediately today, **Sharma Auto Works (67% Match)** is just 1 km away and has immediate availability, though they generally handle Marutis and Hyundais. Which would you prefer to book?"*  
This logic makes your AI incredibly powerful and sets your platform apart from standard directories.  
Would you like to build out the **Customer Profile Database** next, so the AI can remember their vehicle details, past invoices, and service preferences for future bookings?

# concerns/issues

Building a database that predicts and diagnoses vehicle issues based on brand, model, age, and kilometers driven is the absolute holy grail of automotive AI. This is what we call a **Predictive Maintenance & Diagnostic Engine**.  
To make your AI truly smart, a single flat table won't work. If a customer says "my car is vibrating," the AI needs to know if the car has 10,000 km (probably wheel balancing) or 80,000 km (probably engine mounts).  
To handle all possible scenarios—from predicting failures to diagnosing live customer complaints—you need a relational schema split into three logical tables. Here is the highly optimized database structure.

### **Table 1: Vehicle\_Issues\_Master (The Diagnostic Dictionary)**

This table defines every possible thing that can go wrong with a car, regardless of the brand. It acts as the core encyclopedia for the AI.

| Column Name | Description / Logic for AI |
| :---- | :---- |
| **Issue\_ID** | Unique ID for the specific mechanical or electrical fault (e.g., ISS-CLUTCH-01). |
| **Issue\_Name** | Technical name of the problem (e.g., Clutch Plate Wear, Brake Pad Depletion, DPF Clogging). |
| **System\_Category** | Engine, Transmission, Braking, Electrical, Suspension, HVAC, Body. |
| **Severity\_Level** | **Critical** (Stop driving immediately), **Moderate** (Fix soon), **Low** (Fix at next service). |
| **Is\_Safety\_Risk** | Boolean (Yes/No). If "Yes", the AI emphasizes urgency to the customer (e.g., brake failure). |
| **Standard\_OBD2\_Code** | Generic error codes (e.g., P0300 for engine misfire) to cross-reference if a mechanic plugs in a scanner. |
| **Resolution\_Service\_ID** | Links directly to your Services/Parts tables to automatically generate an estimate. |

### **Table 2: Predictive\_Failure\_Matrix (The "When will it break?" Engine)**

This is where the magic happens. The AI uses this table to proactively warn customers about upcoming issues based on their vehicle's exact age and mileage, or to narrow down a vague complaint.

| Column Name | Description / Logic for AI |
| :---- | :---- |
| **Prediction\_ID** | Unique ID for this specific prediction rule (e.g., PRED-SWIFT-045). |
| **Issue\_ID** | Links back to Table 1 (e.g., ISS-TIMING-BELT). |
| **Vehicle\_Make** | Brand (e.g., Hyundai, Maruti Suzuki, Tata). |
| **Vehicle\_Model** | Specific model (e.g., Creta, Swift, Nexon). *Can be set to "ALL" for generic wear.* |
| **Fuel\_Type** | Petrol, Diesel, CNG, EV. (Crucial: Diesel cars face DPF issues at 40k km; EVs do not). |
| **Risk\_Start\_KM** | The mileage where this issue typically begins (e.g., 60,000 km). |
| **Risk\_End\_KM** | The mileage where failure is almost certain if not replaced (e.g., 80,000 km). |
| **Risk\_Start\_Age\_Months** | Time-based degradation, like rubber belts or battery life (e.g., 48 months). |
| **Probability\_Score** | **High, Medium, Low.** Helps the AI prioritize which issues to suggest first. |

### **Table 3: Symptom\_Mapping (The Natural Language Bridge)**

Customers rarely know the technical name of a problem. They describe *symptoms*. This table teaches the AI how to translate customer slang into technical issues.

| Column Name | Description / Logic for AI |
| :---- | :---- |
| **Symptom\_ID** | Unique ID for the customer's complaint (e.g., SYM-NOISE-01). |
| **Issue\_ID** | Links back to Table 1 to connect the symptom to the root cause. |
| **Customer\_Keywords** | Array of search tags (e.g., "shaking at high speed", "steering vibration", "wobbling"). |
| **Sensory\_Category** | Sound (squeak, grind), Feeling (vibration, pulling), Sight (smoke, leaks), Smell (burning, sweet). |
| **AI\_Diagnostic\_Question** | A follow-up question the AI must ask to confirm the issue. (e.g., "Does the steering vibrate only when braking, or at all times while driving over 80km/h?"). |

### **How the AI Uses This Data (The Logic in Action)**

Here is how your AI will combine these tables to assist a customer:  
**Scenario: A customer with a 5-year-old Diesel Hyundai Creta driven for 75,000 km sends a message: *"My car feels sluggish and there is black smoke."***

1. **Symptom Matching:** The AI scans Table 3 for "sluggish" and "black smoke" and flags potential Issue\_IDs (e.g., Clogged Air Filter, EGR Valve Blockage, DPF Clogging, Worn Turbo).  
2. **Predictive Filtering:** The AI cross-references the customer's car details against Table 2.  
   * It sees the car is a **Diesel**.  
   * It sees the mileage is **75,000 km**.  
   * It finds that for a Diesel Creta between 60,000 \- 80,000 km, the Probability\_Score for a clogged DPF (Diesel Particulate Filter) or Carbon Buildup is extremely **High**.  
3. **Intelligent Response:** The AI checks Table 1 for the severity and resolution, and responds to the customer:  
4. *"Since your Diesel Creta has crossed 70,000 km, sluggish pick-up combined with black smoke is most likely due to a clogged Diesel Particulate Filter (DPF) or heavy carbon buildup in the EGR valve. This is a moderate severity issue that will reduce your fuel efficiency. I recommend our 'Throttle & Intake Cleaning' service. Would you like me to share an estimate for this?"*

By structuring the data this way, your AI moves from being a basic chatbot to a highly skilled virtual service advisor.  
Would you like to explore how to integrate OBD2 scanner codes into this schema so the AI can read exact error data straight from the mechanic's scanning tool?

# Cost

To accurately calculate, estimate, and explain total service costs in the Indian auto repair market, a single flat table will quickly become unmaintainable. Service costs in India depend on distinct components—such as **differing GST rates on labor (18%) vs. auto parts (usually 18%–28%)**, **vehicle segment sizing**, **fluid capacities**, and **OEM vs. Aftermarket sourcing**.  
To enable an AI assistant to generate precise, itemized estimates and transparent invoice breakdowns, use the relational schema below divided into **5 structured tables**.

### **Table 1: Service\_Master (Service Definitions & Base Labor)**

This table defines every service offered by the garage and sets the baseline labor requirement.

| Column Name | Data Type | Description / Logic for AI |
| :---- | :---- | :---- |
| Service\_ID | String (PK) | Unique identifier for the service (e.g., SRV-PERIODIC-10K, SRV-BRAKE-PAD-FRONT). |
| Service\_Name | String | Standard service title (e.g., "10,000 km Periodic Maintenance Service", "Front Brake Pad Replacement"). |
| Service\_Category | Enum | Periodic\_Service, Running\_Repair, Denting\_Painting, AC\_Service, Wheel\_Care, Detailing. |
| Standard\_Labor\_Hours | Decimal | Time required to perform the job (e.g., 1.5 hours). Used to compute labor cost dynamically. |
| Is\_Package | Boolean | TRUE if it bundles multiple sub-services and parts (e.g., General Service); FALSE for standalone repairs. |

### **Table 2: Labor\_Cost\_Matrix (Segment-Based Labor Rates)**

Labor charges in India vary significantly based on whether the car is an entry-level hatchback or a luxury SUV. This table maps labor charges to vehicle categories.

| Column Name | Data Type | Description / Logic for AI |
| :---- | :---- | :---- |
| Labor\_Rate\_ID | String (PK) | Unique ID (e.g., LBR-HATCH-01, LBR-SUV-01). |
| Service\_ID | String (FK) | Links to Service\_Master.Service\_ID. |
| Vehicle\_Segment | Enum | Hatchback, Compact\_Sedan, Executive\_Sedan, Compact\_SUV, Mid\_SUV, Luxury\_SUV. |
| Base\_Labor\_Cost\_INR | Decimal | Base labor amount in INR before tax (e.g., ₹450 for Hatchback vs ₹850 for SUV). |
| Labor\_GST\_Percent | Decimal | Fixed at **18.00%** (Standard GST for automotive repair labor services in India). |
| Total\_Labor\_Cost\_Inc\_Tax | Decimal (Formula) | Calculated as: Base\_Labor\_Cost\_INR \* 1.18. |

### **Table 3: Service\_Parts\_BOM (Bill of Materials & Fluid Capacities)**

When a service is selected, the AI uses this table to fetch all required replacement parts, gaskets, and fluids for that specific vehicle engine/variant.

| Column Name | Data Type | Description / Logic for AI |
| :---- | :---- | :---- |
| BOM\_ID | String (PK) | Unique Bill of Materials entry ID (e.g., BOM-SWIFT-K12-10K). |
| Service\_ID | String (FK) | Links to Service\_Master.Service\_ID. |
| Variant\_ID | String (FK) | Links to the specific vehicle engine variant (e.g., Maruti K12 Petrol, Hyundai 1.5 CRDi Diesel). |
| Part\_ID | String (FK) | Links to the Spare Parts database (e.g., PRT-OIL-FILTER-01, PRT-5W30-SYNTH-OIL). |
| Required\_Quantity | Decimal | Number of units required (e.g., 1 Oil Filter, 3.5 Liters of Engine Oil). |
| Unit\_Of\_Measure | Enum | Units, Liters, Milliliters, Grams, Sets. |

### **Table 4: Spare\_Parts\_Cost\_Master (Parts Pricing, Sourcing & Taxes)**

This table tracks the financial metrics of spare parts, including MRP, garage cost, GST slabs, and sourcing tier options.

| Column Name | Data Type | Description / Logic for AI |
| :---- | :---- | :---- |
| Part\_Cost\_ID | String (PK) | Unique pricing entry (e.g., PRC-PAD-FRONT-CRETA). |
| Part\_ID | String (FK) | Unique part identification code. |
| Part\_Grade\_Type | Enum | OEM (Original Equipment Manufacturer), OES (Original Equipment Supplier), Aftermarket\_Premium, Aftermarket\_Budget. |
| Part\_MRP\_INR | Decimal | Maximum Retail Price inclusive of taxes printed on the box. |
| Garage\_Purchase\_Cost\_INR | Decimal | Cost at which the garage buys from distributor (used by AI to evaluate profit margin). |
| Part\_GST\_Percent | Decimal | Auto parts GST slab: usually **28%** for standard components, **18%** for select oils/batteries. |
| Selling\_Price\_Excl\_Tax | Decimal | Price charged to customer before tax (Calculated from MRP and Part GST %). |

### **Table 5: Consumables\_&\_Auxiliary\_Charges (Sundries & Shop Fees)**

Indian workshops frequently include small operational charges (rust-off sprays, degreasers, shop rags, waste disposal fees). Storing them here allows the AI to provide standard or customizable add-ons.

| Column Name | Data Type | Description / Logic for AI |
| :---- | :---- | :---- |
| Aux\_Charge\_ID | String (PK) | Unique ID (e.g., AUX-CONSUMABLES-STD). |
| Charge\_Name | String | Name on bill (e.g., "Workshop Consumables & Sundries", "Battery Environmental Disposal Fee", "Wheel Balancing Weights"). |
| Calculation\_Type | Enum | Flat\_Fee (e.g., ₹150) or Percentage\_Of\_Labor (e.g., 3% of Total Labor). |
| Charge\_Value | Decimal | Fixed amount or percentage multiplier. |
| Aux\_GST\_Percent | Decimal | Standard tax rate applicable (usually 18%). |
| Is\_Mandatory | Boolean | TRUE if auto-added to every invoice; FALSE if optional. |

### **Summary Calculation Formula for AI Assistant**

When a customer requests a quote for a specific car model, the AI calculates the final estimate using this formula:  
$$\\text{Total Estimate} \= (\\text{Labor Base} \\times 1.18) \+ \\sum \\left( \\text{Part Price Excl. Tax} \\times \\left(1 \+ \\frac{\\text{Part GST \\%}}{100}\\right) \\times \\text{Qty} \\right) \+ \\text{Consumables}$$

#### **Example AI Estimate Output generated from these tables:**

**Estimate for Hyundai Creta 1.6 Diesel (10,000 km Service):**

* **Labor Charge:** ₹850 \+ ₹153 (18% GST) \= **₹1,003**  
* **Engine Oil (5W-30 Synthetic, 5.3 L @ ₹650/L incl. 18% GST):** **₹3,445**  
* **Oil Filter (OEM, incl. 28% GST):** **₹380**  
* **Workshop Consumables & Sundries (Flat Fee):** **₹150**

**Total Cost:** **₹4,978 (Incl. all taxes)**  
