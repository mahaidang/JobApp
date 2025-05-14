// Reducer KHÔNG THỂ là hàm bất đồng bộ!
const MyUserReducer = (current, action) => {
    switch (action.type) {
        case "login":
            return action.payload;
        case "logout":
            // Không thể có "await" trong reducer
            return null;
    }
    
    return current;
};

export default MyUserReducer;