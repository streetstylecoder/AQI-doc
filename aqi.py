import streamlit as st
from streamlit_js_eval import streamlit_js_eval, copy_to_clipboard, create_share_link, get_geolocation
import json
import requests
import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_echarts import st_echarts
import pandas as pd
import pydeck as pdk
from llama_index import VectorStoreIndex, ServiceContext, Document
from llama_index.llms import OpenAI
import openai
from llama_index import SimpleDirectoryReader
import os
from bs4 import BeautifulSoup
import random

os.environ['OPENAI_API_KEY'] = st.secrets['OPENAI_API_KEY']

st.session_state['comps']=''


@st.cache_resource # Cache the function so it doesn't re-scrape when the page refreshes (unless the URL changes)
def get_amazon_product_details(url):
    custom_headers = {
'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
'accept-language': 'en-GB,en;q=0.9',
}
    
    try:
        response = requests.get(url, headers=custom_headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Here you need to identify the tags where the product information is located.
            # This will vary depending on the Amazon product page layout and may change over time.
            # This is just a placeholder example and you'll need to inspect the Amazon page to find the correct tags.
            # print(soup)
            title = soup.find(id='productTitle').get_text().strip()
            description= soup.find(id='feature-bullets').get_text().strip() 
            div = soup.find('div', id='imgTagWrapperId')
            reviews=soup.find(id='cm-cr-dp-review-list').get_text().strip() 
            price_span = soup.find('span', class_='a-price-whole')

            if price_span:
                price = price_span.get_text(strip=True)
                
            else:
                print("Price span not found.")
            

            # Initialize src to None
            src = None

            # If the div is found, look for the img tag inside the div
            if div:
                img = div.find('img')
                # If the img tag is found, get the src attribute
                if img and img.has_attr('src'):
                    src = img['src']
            
            
            # You can add more details by finding more tags containing relevant information.
            
            return {
                "Title": title,
                "desc": description,
                "image":src,
                "reviews":reviews  ,
                "price":price
            }
        else:
            return {"error": "Failed to retrieve the product details, status code: " + str(response.status_code)}
    except Exception as e:
        return {"error": "An error occurred: " + str(e)}
    



if "messages" not in st.session_state.keys(): # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "hello how may I help you ?","avatar":"human"}
    ]



@st.cache_resource(show_spinner=False)
def load_data():
    with st.spinner(text="Loading DR.otrivine guide"):
        reader = SimpleDirectoryReader(input_dir="./data", recursive=True)
        docs = reader.load_data()
        service_context = ServiceContext.from_defaults(llm=OpenAI(model="gpt-3.5-turbo", temperature=0.1,system_prompt="I am doctor otrivine , I help people consult problems related to air pollution and suggest them otrivine products with their complete description.I only suggest medical advises and suggest otrivine products along with my answers"))
        index = VectorStoreIndex.from_documents(docs, service_context=service_context)
        return index
   


@st.cache_resource(show_spinner=False)
def load_advisor():
    with st.spinner(text="Loading the otrivine Dr otrivineer"):
        reader = SimpleDirectoryReader(input_dir="./product_buy_guide", recursive=True)
        docs = reader.load_data()
        service_context = ServiceContext.from_defaults(llm=OpenAI(model="gpt-3.5-turbo",temperature=0.8,system_prompt="I am doctor otrivine , I help people people find the right air purifiers accroding to their budget and analysing the pollutant levels at their location."))
        index = VectorStoreIndex.from_documents(docs, service_context=service_context)
        return index

# 1=sidebar menu, 2=horizontal menu, 3=horizontal menu w/ custom menu
EXAMPLE_NO = 1


def streamlit_menu(example=1):
    if example == 1:
        # 1. as sidebar menu
        with st.sidebar:
            selected = option_menu(
                menu_title="otrivine air",  # required
                options=["AQI", "Dr Otrivine", "Product Research"],  # required
                icons=["tree", "box", "envelope"],  # optional
                menu_icon="cast",  # optional
                default_index=0,  # optional
            )
        return selected

    if example == 2:
        # 2. horizontal menu w/o custom style
        selected = option_menu(
                menu_title="otrivine air",  # required
                options=["AQI", "Dr Otrivine", "Product Research"],  # required
                icons=["tree", "box", "envelope"],  # optional
                menu_icon="cast",  # optional
                default_index=0,  # optional
            )
        return selected

    if example == 3:
        # 2. horizontal menu with custom style
        selected = option_menu(
                menu_title="otrivine air",  # required
                options=["AQI", "Dr Otrivine", "Product Research"],  # required
                icons=["tree", "box", "envelope"],  # optional
                menu_icon="cast",  # optional
                default_index=0,  # optional
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "25px"},
                "nav-link": {
                    "font-size": "25px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "green"},
            },
        )
        return selected


selected = streamlit_menu(example=EXAMPLE_NO)

st.session_state['latitude'] = 28.50
st.session_state['longitude'] = 77.08
    
loc = get_geolocation()
if loc:
    st.session_state['latitude'] = loc['coords']['latitude']
    st.session_state['longitude'] = loc['coords']['longitude']
    
else:
    # st.error('Geolocation data is not available.')
    print("location issue")
api_key = "6f521af880e69ef3c4fb7252a5ec7c72"  # Replace with your actual API key

@st.cache_resource
def get_air_pollution_data(lat, lon):
    """Fetch and return air pollution data for given latitude and longitude."""
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
    response = requests.get(url)
    return response.json()

@st.cache_resource
def get_location_data(lat, lon):
    """Fetch and return location data for given latitude and longitude."""
    url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={api_key}"
    response = requests.get(url)
    return response.json()



def get_health_effects(value, pollutant):
    health_effects = {
        'so2': [
        "Minimal or no health impacts.",
        "Irritation of eyes, nose, throat; individuals with asthma may experience breathing difficulties.",
        "Increased respiratory symptoms, such as shortness of breath and coughing, in sensitive populations.",
        "Risk of lung function impairment and aggravation of cardiovascular diseases.",
        "Severe respiratory and cardiovascular impact; potential for increased mortality."
    ],
    'no2': [
        "Minimal or no health impacts.",
        "Minor respiratory effects in sensitive individuals; generally no significant health effects expected in the general population.",
        "Increased inflammation of the airways; potential exacerbation of asthma and decreased lung function.",
        "Increased risk of respiratory infections; potential for long-term effects on lung structure and function.",
        "Severe respiratory effects including risk of developing asthmatic conditions; increased risk of respiratory infections."
    ],
    'pm10': [
        "Minimal or no health impacts.",
        "May cause minor airway irritation in sensitive individuals.",
        "Potential aggravation of heart and lung disease and premature mortality in individuals with pre-existing conditions. May increase respiratory symptoms in sensitive populations.",
        "Increased likelihood of reduced lung function and inflammation of the lungs, which can lead to health issues for sensitive groups.",
        "Serious aggravation of heart and lung diseases leading to increased mortality. Extended exposure can affect healthy individuals."
    ],
    'pm2_5': [
        "Minimal or no health impacts.",
        "Potential for slight irritation of the airways; possible discomfort for sensitive individuals.",
        "Increased risk of respiratory symptoms and reduced lung function, particularly in individuals with asthma or heart conditions.",
        "High likelihood of adverse effects on the heart and lungs, which may result in health complications for individuals with pre-existing conditions.",
        "Severe health effects including increased emergency room visits, hospital admissions, and mortality. Health impacts may be experienced during light physical activity."
    ],
    'o3': [
        "Minimal or no health impacts.",
        "May cause minor respiratory tract irritation and discomfort.",
        "Increased risk of respiratory tract irritation and inflammation. Possible exacerbation of lung diseases like asthma, leading to symptoms such as chest tightness and wheezing.",
        "Significant risk of triggering asthma attacks and other serious respiratory conditions. Prolonged exposure may lead to reduced lung function.",
        "Severe risk of triggering serious respiratory conditions even during light physical activities. Prolonged exposure can lead to chronic respiratory diseases."
    ],
    'co': [
        "Minimal or no health impacts at low outdoor concentrations.",
        "Increased fatigue in healthy people and potential for chest pain in people with heart disease.",
        "May cause significant health effects including fatigue, chest pain, and impaired vision and coordination. Individuals with heart conditions are at increased risk.",
        "May lead to more severe symptoms such as impaired vision and coordination, headaches, dizziness, confusion, and nausea. It can worsen cardiovascular conditions.",
        "At very high levels, can cause severe symptoms up to and including death, particularly in vulnerable populations."
    ]
    }
    
    level, _ = get_level_color(value, pollutant)
    # Subtract 1 because levels are 1-indexed but list indices are 0-indexed
    return health_effects[pollutant][level - 1]




if selected == "AQI":
    st.title(f"AQI monitor")
    
    st.write("your coordinates",st.session_state['latitude'],st.session_state['longitude'])
    if 'latitude' in st.session_state and 'longitude' in st.session_state:
    # Construct the API URL using session state values
        if 'latitude' in st.session_state and 'longitude' in st.session_state:
    # Get air pollution data
            air_pollution_data = get_air_pollution_data(st.session_state['latitude'], st.session_state['longitude'])
            res=air_pollution_data
            aqi = air_pollution_data["list"][0]["main"]["aqi"]
            st.write(f"Air Quality Index (AQI): {aqi}")
            aqi_levels = {
            1: ("Good", "#55AE3A"),
            2: ("Fair", "#A3C853"),
            3: ("Moderate", "#FFF833"),
            4: ("Poor", "#F29C33"),
            5: ("Very Poor", "#E93F33"),
        }
            aqi_levels_map = {
    1: ("Good", "#55AE3A", 1000),
    2: ("Fair", "#A3C853", 2000),
    3: ("Moderate", "#FFF833", 3000),
    4: ("Poor", "#F29C33", 4000),
    5: ("Very Poor", "#E93F33", 5000),
}

            # Get location data
            location_data = get_location_data(st.session_state['latitude'], st.session_state['longitude'])
            if location_data:
                location_name = location_data[0]['name']
                location_state = location_data[0]['state']
                location_country = location_data[0]['country']
                st.info(f"Showing results for address: {location_name}, {location_state}, {location_country}")
                latitude = st.session_state.get('latitude', 0)  # Replace 0 with a default latitude if needed
                longitude = st.session_state.get('longitude', 0)  # Replace 0 with a default longitude if needed

                _, hex_color, radius = aqi_levels_map[aqi]
                rgba_color = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)] + [140]  # Add the alpha value

                # Set up a PyDeck layer
                layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=[{
                        'position': [longitude, latitude],
                        'color': rgba_color,
                        'radius': radius,
                    }],
                    get_position='position',
                    get_color='color',
                    get_radius='radius',
                )   

                # Set the view state for the map
                view_state = pdk.ViewState(
                    latitude=latitude,
                    longitude=longitude,
                    zoom=11
                )

                # Render the map with PyDeck
                r = pdk.Deck(layers=[layer], initial_view_state=view_state, map_style="mapbox://styles/mapbox/light-v9")
                st.pydeck_chart(r)

        
        # Get the AQI level and color based on the AQI value
        aqi_level, color = aqi_levels.get(aqi, ("Hazardous", "#AF2D24"))

        # ECharts options
        options = {
            "series": [{
                "type": "gauge",
                "startAngle": 90,
                "endAngle": -270,
                "pointer": {
                    "show": False
                },
                "progress": {
                    "show": True,
                    "overlap": False,
                    "roundCap": True,
                    "clip": False,
                    "itemStyle": {
                        "color": color
                    }
                },
                "axisLine": {
                    "lineStyle": {
                        "width": 15
                    }
                },
                "axisTick": {
                    "show": False
                },
                "splitLine": {
                    "show": False,
                    "distance": 0,
                    "length": 10
                },
                "axisLabel": {
                    "show": False,
                    "distance": 50
                },
                "data": [{
                    "value": aqi * 20,  # Scale the value to use the full range of the gauge
                    "name": " ",
                    "title": {
                        "offsetCenter": ["0%", "-20%"]
                    },
                    "detail": {
                        "valueAnimation": True,
                        "offsetCenter": ["0%", "0%"],
                        "formatter": f"{aqi_level}\n\n{aqi}"
                    }
                }],
                "detail": {
                    "fontSize": 20,
                    "fontWeight": "bolder",
                    "color": "auto"
                }
            }]
        }

        # Render the chart
        st_echarts(options=options, height="300px")

        # components_charts
        pollutant_ranges = {
        'so2': [(0, 20), (20, 80), (80, 250), (250, 350), (350, float('inf'))],
        'no2': [(0, 40), (40, 70), (70, 150), (150, 200), (200, float('inf'))],
        'pm10': [(0, 20), (20, 50), (50, 100), (100, 200), (200, float('inf'))],
        'pm2_5': [(0, 10), (10, 25), (25, 50), (50, 75), (75, float('inf'))],
        'o3': [(0, 60), (60, 100), (100, 140), (140, 180), (180, float('inf'))],
        'co': [(0, 4400), (4400, 9400), (9400, 12400), (12400, 15400), (15400, float('inf'))],
    }

        # Define the colors for each level
        colors = ["#55AE3A", "#A3C853", "#FFF833", "#F29C33", "#E93F33", "#AF2D24"]

        # Function to determine the level and color of a given value for a pollutant
        def get_level_color(value, pollutant):
            for i, (low, high) in enumerate(pollutant_ranges[pollutant]):
                if low <= value < high:
                    return i + 1, colors[i]
            return 6, colors[-1]

        # Function to create ECharts gauge options for a given pollutant
        def create_gauge_options(value, pollutant):
            level, color = get_level_color(value, pollutant)
            return {
                "series": [{
                    "type": "gauge",
                    "startAngle": 90,
                    "endAngle": -270,
                    "pointer": {
                        "show": False
                    },
                    "progress": {
                        "show": True,
                        "overlap": False,
                        "roundCap": True,
                        "clip": False,
                        "itemStyle": {
                            "color": color
                        }
                    },
                    "axisLine": {
                        "lineStyle": {
                            "width": 15
                        }
                    },
                    "axisTick": {
                        "show": False
                    },
                    "splitLine": {
                        "show": False,
                        "distance": 0,
                        "length": 10
                    },
                    "axisLabel": {
                        "show": False,
                        "distance": 50
                    },
                    "data": [{
                        "value": level * 20,  # Scale the value to use the full range of the gauge
                        "name": pollutant.upper(),
                        "title": {
                            "offsetCenter": ["0%", "-30%"]
                        },
                        "detail": {
                            "valueAnimation": True,
                            "offsetCenter": ["0%", "0%"],
                            "formatter": f"{value} µg/m³"
                        }
                    }],
                    "detail": {
                        "fontSize": 20,
                        "fontWeight": "bolder",
                        "color": "auto"
                    }
                }]
            }

        # Display the charts
        st.title("Pollutant Concentrations")
        components = {k: v for k, v in res["list"][0]["components"].items() if k in pollutant_ranges}
        st.session_state['comps']=components
        component_iterator = iter(components.items())

        for pollutant, value in component_iterator:
            # Create two columns
            col1, col2 = st.columns(2)

            # Display the first chart in the first column
            with col1:
                st_echarts(options=create_gauge_options(value, pollutant), height="300px")
                st.markdown(f"**{pollutant.upper()} Level:** {value} µg/m³")
                st.info(get_health_effects(value, pollutant))

            # Get the next item from the iterator for the second column, if it exists
            try:
                next_pollutant, next_value = next(component_iterator)
                with col2:
                    st_echarts(options=create_gauge_options(next_value, next_pollutant), height="300px")
                    st.markdown(f"**{next_pollutant.upper()} Level:** {next_value} µg/m³")
                    st.info(get_health_effects(next_value, next_pollutant))
            except StopIteration:
                # If there are no more items, break from the loop
                break
if selected == "Dr Otrivine":
    st.title("Dr.otrivine")
    index = load_data()
    chat_engine = index.as_chat_engine(chat_mode="context", verbose=True)

    if prompt := st.chat_input("Please enter your question here"): # Promp for user input and save to chat history
        st.session_state.messages.append({"role": "user", "content": prompt })

    for message in st.session_state.messages: # Display the prior chat messages
        if(message["role"]=="assistant"):
            with st.chat_message(message["role"]):
                st.write(message["content"])
        else:
            with st.chat_message(message["role"]):
                st.write(message["content"])

            

    # If last message is not from assistant, generate a new response
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                print(prompt)
                response = chat_engine.chat(prompt+ f"assume you are suggesting people products from otrivine according to the problems they are facing, anaylse the person's problem tell them the possible symptoms considering the air pollutants at their location is {st.session_state['comps']} then provide details containing the components 'name' containing the otrivine product they should use 'desc' description about that otrivine product 'extra care' extra care and suggestions that person should take to solve thier problem")
                st.write(response.response)
                message = {"role": "assistant", "content": response.response}
                st.session_state.messages.append(message) # Add response to message history
                folder_path = './images'  # Replace with the path to your folder

                # List all files in the folder
                image_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

                # Choose a random image file
                selected_image = random.choice(image_files)

                # Display the image
                st.image(os.path.join(folder_path, selected_image))

                # Write the name of the image
                st.write(selected_image)

if selected == "Product Research":
    product_url = st.text_input("Enter the Amazon product URL", "")
    if st.button("Get Product Details"):
        if product_url:
            try:
                # Call the function to scrape product details
                product_details = get_amazon_product_details(product_url)
                
                # Check if the product details are valid
                if not product_details or 'image' not in product_details:
                    st.error("Failed to retrieve product details. Please check the URL and try again.")
                else:
                    st.image(product_details['image'])
                    st.header(product_details['Title'])
                    st.info("Rs:" + product_details['price'])
                    
                    index = load_advisor()

                    query = f"assume you are guiding a novice person who has no knowledge about buying an air purifier. They will provide you details of an air purifier and you have to analyse if it is a good product and if they should consider buying it. According to your knowledge, please suggest if the air purifier with the description {product_details['Title']} {product_details['desc']} priced at {product_details['price']} having reviews {product_details['reviews']} would be good for me. Tell me if the reviews indicate any problems with it. If concentration levels at my location are {st.session_state['comps']}, please analyse the product, the concentration levels at my location, its reviews. Focus your answers only on the product description I provided to you and tell me about this product."

                    chat_engine = index.as_chat_engine(chat_mode="context", verbose=True)
                    with st.spinner("Loading..."):
                        try:
                            response = chat_engine.chat(query)
                            st.write(response.response)
                        except Exception as e:
                            st.error("Failed to get a response from the chat engine. Please try again later.")
            except Exception as e:
                st.error("An error occurred while fetching the product details. Please check the URL and try again.")

            
           
    

