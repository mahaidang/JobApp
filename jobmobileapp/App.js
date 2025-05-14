import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { useContext, useEffect, useReducer } from "react";
import { Icon } from "react-native-paper";
import Home from "./components/Home/Home";
import Login from "./components/User/Login";
import { MyDispatchContext, MyUserContext } from "./configs/MyContexts";
import MyUserReducer from "./reducers/MyUserReducer";
import Profile from "./components/User/Profile";


const Stack = createNativeStackNavigator();

const Tab = createBottomTabNavigator();
const TabNavigator = () => {
  return (
    <Tab.Navigator>
      <Tab.Screen name="index" component={Home} options={{ title: "Công việc", tabBarIcon: () => <Icon source="home" size={20} />}}
      />
      <Tab.Screen name="profile" component={Profile} options={{title: "Tài khoản",tabBarIcon: () => <Icon source="logout" size={20} />}} />        
    </Tab.Navigator>
  );
};
const MainStackNavigator = () => {
  const user = useContext(MyUserContext);

  return (
    <Stack.Navigator>
      {user === null?<>
        <Stack.Screen name="login" component={Login} options={{ title: "Đăng nhập" }} />
      </>:<>
        <Stack.Screen name="tabs" component={TabNavigator} options={{headerShown: false}}/>
      </>}
      
    </Stack.Navigator>
  );
}

const App = () => {
  const [user, dispatch] = useReducer(MyUserReducer, null);

  useEffect(() => {
    // Khi user thay đổi thành null (đăng xuất), stack sẽ tự reset
    console.log('User state changed:', user);
  }, [user]);

  return (
    <MyUserContext.Provider value={user}>
      <MyDispatchContext.Provider value={dispatch}>
        <NavigationContainer>
            <MainStackNavigator/>
        </NavigationContainer>
      </MyDispatchContext.Provider>
    </MyUserContext.Provider>
  );
}

export default App;