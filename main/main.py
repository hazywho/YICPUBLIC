import AutoFocus
import streamlit as st
import cv2

#initialize prerequisites
if "driver" not in st.session_state:
    st.session_state.driver = None
if "annotatedImgs" not in st.session_state:
    st.session_state.annotatedImgs = None
if "response" not in st.session_state:
    st.session_state.response = None
if "imageIndex" not in st.session_state:
    st.session_state.imageIndex = 0
if "imgs" not in st.session_state:
    st.session_state.imgs = None
main_c1,main_c2 = st.columns([1,2])

#page configs
st.set_page_config(layout="wide")
st.title("OceanGate")

with main_c1:
    #DATA COLLECTION
    slideArea = st.text_input("insert your measured slide area here", value="400", placeholder="400")
    #later need mroe info for water data
    pH = st.number_input("pH", min_value=0.0, max_value=14.0, value=7.0, step=0.1)
    Do = st.number_input("Dissolved Oxygen (DO)", min_value=0.0, value=6.0, step=0.1, help="mg/L")
    BOD = st.text_input("Biochemical Oxygen Demand (BOD)", value ="7", placeholder="mg/L")
    COD = st.text_input("Chemical Oxygen Demand (COD)", value ="7", placeholder="mg/L")
    TDS = st.text_input("Total Suspended Solids (TDS)", value ="7", placeholder="mg/L")
    ammonia = st.text_input("Nitrogen (Ammonia)", value ="7", placeholder="mg/L")
    waterData = {"pH": pH,
                "Dissolved Oxygen": Do,
                "Biochemical Oxygen Demand": int(BOD),
                "Chemical Oxygen Demand": int(COD),
                "Nitrogen (ammonia)": int(ammonia)}


    # PROCESS STARTUP
    if st.button("submit data and begin"):
        st.session_state.driver = AutoFocus.main(slideArea=slideArea, waterData=waterData)
        st.session_state.annotatedImgs = None
        st.session_state.response=None
        
        
    #DATA VISUALISATION   
    if "driver" in st.session_state:
        if st.button("reset", icon="🔄"):
            with st.spinner("reset in progress..."):
                st.session_state.driver._clearCalibration(0)
            st.write("done")
            
        if st.button("start taking photo", type="primary"): #main driver function
            with st.spinner("machine running :3"):
                status = st.session_state.driver.getBestImg()
                if status:
                    response, origImageList, annotatedImageList = st.session_state.driver.moveAroundAndProcess()
                    st.session_state.annotatedImgs = annotatedImageList
                    st.session_state.response = response
                    st.session_state.imgs = origImageList
                else:
                    st.write("calibration error :(")
                    

with main_c2:
    #displays when theres data.
    annoList:list = st.session_state.annotatedImgs
    if annoList is not None: 
        st.divider()
        st.header("Results")
        n_images=len(annoList)
        c1, _, c2= st.columns([1,8,1])
        st.session_state.imageIndex=0
        
        #movement functions
        with c1:
            if st.button("prev"):
                st.session_state.imageIndex = (st.session_state.imageIndex-1)%n_images
        with c2:
            if st.button("next"):
                st.session_state.imageIndex = (st.session_state.imageIndex+1)%n_images
        
        #download functions
        st.subheader("Download images")
        c_index = st.session_state.imageIndex
        _, current_image_bytes = cv2.imencode(".png", st.session_state.imgs[c_index])
        st.write(f"AI analysis: {st.session_state.response}")
        st.image(
            annoList[c_index],
            caption=f"Captured Images {c_index + 1} of {n_images}. (original versions saved in folder)",
            use_column_width=True,
        )
        st.subheader("download")
        st.download_button(
            label="Download Current Image",
            data=current_image_bytes.tobytes(), # .tobytes() converts the buffer to raw bytes
            file_name="image.png",
            mime="image/png" # Tells the browser it's a PNG file
        )


#closing utility function.
if st.button("finish & return results"):
    st.session_state.annotatedImgs = None