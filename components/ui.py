import streamlit as st
import asyncio
from components.api import search_company, fetch_brand_details
from components.utils import is_white_svg, is_white_image, create_zip_file
import aiohttp
import traceback

async def fetch_logos(company_names, api_key, _progress_bar):
    logos = []
    progress_step = 1 / len(company_names) if company_names else 1

    async with aiohttp.ClientSession() as session:
        # Search for brands
        search_tasks = [search_company(session, name) for name in company_names]
        search_results = await asyncio.gather(*search_tasks)

        for i, (company_name, search_result) in enumerate(zip(company_names, search_results)):
            if "error" in search_result:
                logos.append((company_name, None, None, f"Error searching brand: {search_result['error']}", False))
                continue

            domain = search_result.get('domain')
            brand_data = await fetch_brand_details(session, domain, api_key)
            if "error" in brand_data:
                logos.append((company_name, None, None, f"Error fetching brand details: {brand_data['error']}", False))
                continue

            logo_url = None
            for logo in brand_data.get('logos', []):
                if logo['type'] == 'logo':
                    for format in logo['formats']:
                        if format['format'] == 'svg':
                            logo_url = format['src']
                            break
                    if logo_url:
                        break

            if not logo_url:
                for logo in brand_data.get('logos', []):
                    if logo['type'] == 'logo':
                        for format in logo['formats']:
                            if format['format'] == 'png':
                                logo_url = format['src']
                                break
                        if logo_url:
                            break

            if not logo_url:
                for logo in brand_data.get('logos', []):
                    if logo['type'] == 'logo':
                        for format in logo['formats']:
                            if format['format'] in ['jpg', 'jpeg']:
                                logo_url = format['src']
                                break
                        if logo_url:
                            break

            if logo_url:
                async with session.get(logo_url) as logo_response:
                    logo_content = await logo_response.read()
                    if logo_url.endswith('.svg'):
                        is_white = is_white_svg(logo_content.decode('utf-8'))
                    else:
                        is_white = is_white_image(logo_content, logo_url.split('.')[-1])
                    logos.append((company_name, logo_url, logo_content, None, is_white))
            else:
                logos.append((company_name, None, None, "No SVG, PNG, or JPG Logo available", False))

            _progress_bar.progress((i + 1) * progress_step)

    return logos

@st.cache_data(ttl=3600)
async def cached_fetch_logos(company_names, api_key):
    return await fetch_logos(company_names, api_key, None)

def display_ui():
    st.markdown("""
        <h1 style="padding: 0px;">Logo Fetcher</h1>
    """, unsafe_allow_html=True)
    st.markdown("""
        <h5 style="padding-bottom: 15px;"><u><i>Bulk Logo Finding</i></u></h5>
    """, unsafe_allow_html=True)

    with st.expander("Intro. / Inst.", icon="ℹ️"):
        st.info("""
        This is a simple application designed to make logo retrieval faster via the Brandfetch API. 
        To use this application, you need to:
        1. Navigate to [Brandfetch Developers](https://developers.brandfetch.com/).
        2. Create a developer account (it's free). [With this you'll have 250 free logo searches per month.]
        3. Access your API key from your Brandfetch dashboard.
        4. Enter your API key and the company names in the fields below.

        Once you have entered the company names (comma-separated), the application will fetch the logos (and cache your results during your session, a.k.a until you close the tab), with options to download each logo individually or all at once.
        
        Happy logo-hunting! Major shoutout to the team over at [Brandfetch](https://brandfetch.com/).
        """)

    api_key = st.text_input("Enter Your Brandfetch API Key:", type="password", help="Enter your API key obtained from Brandfetch.")
    
    # Text area for company names
    st.session_state.company_names = st.text_area("Enter Company Names (comma-separated):", value=st.session_state.get("company_names", ""), help="Enter the names of the companies you want to fetch logos for, separated by commas.")
    # Add the attribution line with styling
    st.markdown('<p style="text-align: right; font-size: 14px; color: gray;">Logos & Search provided by <a href="https://brandfetch.com" style="color: gray;">Brandfetch</a></p>', unsafe_allow_html=True)

    # Initialize session state for fetched data and selected files
    if "logos" not in st.session_state:
        st.session_state.logos = []
    if "selected_files" not in st.session_state:
        st.session_state.selected_files = []
    if "select_all" not in st.session_state:
        st.session_state.select_all = False

    # Place "Clear All" and "Fetch Logos" buttons in the same row, with "Fetch Logos" right-aligned
    col1, col2, col3 = st.columns([3, 9.5, 3])
    with col1:
        if st.button("Clear Text Area"):
            st.session_state.company_names = ""

    with col3:
        if st.button("Fetch Logos"):
            if api_key and st.session_state.company_names:
                company_list = [name.strip() for name in st.session_state.company_names.split(',')]
                progress_bar = st.progress(0)
                try:
                    new_logos = asyncio.run(fetch_logos(company_list, api_key, progress_bar))
                    # Cache logos in session state
                    st.session_state.logos.extend(new_logos)
                    st.session_state.selected_files = []
                    st.session_state.select_all = False
                except Exception as e:
                    error_message = traceback.format_exc()
                    st.error(f"An error occurred: {error_message}")
            else:
                st.warning("Please enter both your API key and the company names.")

    # Display previously fetched logos
    if st.session_state.logos:
        st.markdown("##### Cached Logos")
        all_logo_files = []
        white_logo_brands = []

        for company_name, logo_url, logo_content, error, is_white in st.session_state.logos:
            if logo_url:
                extension = 'svg' if 'svg' in logo_url else 'png' if 'png' in logo_url else 'jpg'
                all_logo_files.append((f"{company_name}.{extension}", logo_content))
                if is_white:
                    white_logo_brands.append(company_name)
            else:
                st.write(f"### {company_name}")
                st.write(error)

        # Add a "Select All" checkbox
        st.session_state.select_all = st.checkbox("Select All Logos", st.session_state.select_all)
        if st.session_state.select_all:
            st.session_state.selected_files = [name for name, _, _, _, _ in st.session_state.logos]
        else:
            st.session_state.selected_files = st.multiselect("Select logos to download", [name for name, _, _, _, _ in st.session_state.logos], st.session_state.selected_files)
        
        if st.session_state.selected_files:
            selected_logo_files = [(name, content) for name, content in all_logo_files if name.split('.')[0] in st.session_state.selected_files]
            zip_data = create_zip_file(selected_logo_files)

            st.download_button(
                label="Download Selected Logos",
                data=zip_data,
                file_name="selected_logos.zip",
                mime="application/zip"
            )
        st.toast("Logos have been successfully found and inserted into a folder.")
        
        if white_logo_brands:
            # st.markdown("### Note")
            brands_list = ", ".join([f"**{brand}**" for brand in white_logo_brands])
            st.toast(f"We noticed that you searched and downloaded the following logos: {brands_list}. We just wanted to let you know that these logos are primarily white, so if you don't see them right away, try viewing them against a black background.", icon="🚨")
