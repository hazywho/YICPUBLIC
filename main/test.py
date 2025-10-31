import streamlit as st

class testSubject():
    def __init__(self, x:int = 20, y:int = 20):
        self.x = x
        self.y = y
        
    def printout(self, z:int):
        return self.x+self.y+z
  
if __name__ == "__main__":
    col1, col2 = st.columns(2)
    with col1:
        a = st.text_input(label="A here", placeholder="43")
    with col2:
        b = st.text_input(label="B here", placeholder="34")
    if st.button("submit data and begin"):
        st.session_state.driver=testSubject(int(a), int(b))


    #reset button
    if "driver" in st.session_state:
        if st.button("reset", icon="🔄"):
            with st.spinner():
                st.session_state.driver.printout(10)
            st.write("done")

        if st.button("start taking photo"):
            with st.spinner():
                status = st.session_state.driver.printout(7)
                if status:
                    response = st.session_state.driver.printout(0)
                    st.write(response)
                else:
                    st.write("calibration error")
