import { CLIENT_ID, CLIENT_SECRET } from '@env';
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useContext, useState } from "react";
import { Image, Linking, ScrollView, Text, TouchableOpacity, View } from "react-native";
import { Button, HelperText, TextInput } from "react-native-paper";
import Apis, { authApis, endpoints } from "../../configs/Apis";
import { MyDispatchContext } from "../../configs/MyContexts";
import MyStyles from "../../styles/MyStyles";
import {BASE_URL} from "../../configs/Apis";


const Login = () => {
    const info = [{
        label: 'Tên đăng nhập',
        icon: "text",
        secureTextEntry: false,
        field: "username"
    }, {
        label: 'Mật khẩu',
        icon: "eye",
        secureTextEntry: true,
        field: "password"
    }];
    const [user, setUser] = useState({});
    const [msg, setMsg] = useState(null);
    const [loading, setLoading] = useState(false);
    const dispatch = useContext(MyDispatchContext);

   
    const setState = (value, field) => {
        setUser({...user, [field]: value});
    }

    const validate = () => {
        if (!user?.username || !user?.password) {
            setMsg("Vui lòng nhập tên đăng nhập và mật khẩu!");
            return false;
        } 

        setMsg(null);
        
        return true;
    }

    const login = async () => {
        if (validate() === true) {
            try {
                setLoading(true);
    
                let formData = new FormData();
                formData.append('username', user.username);
                formData.append('password', user.password);
                formData.append('client_id', CLIENT_ID);
                formData.append('client_secret', CLIENT_SECRET);
                formData.append('grant_type', 'password');
    
                let res = await Apis.post(endpoints['login'], formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                });
    
                await AsyncStorage.setItem("token", res.data.access_token);
    
                let u = await authApis(res.data.access_token).get(endpoints['current-user']);
                console.log("Login response:", res.data);
    
                dispatch({
                    "type": "login",
                    "payload": u.data
                });
    
            } catch (ex) {
                console.error(ex);
            } finally {
                setLoading(false);
            }
        }
    };
    
    const handleGoogleLogin = async () => {
        try {
            // Mở trình duyệt đến endpoint Google login
            const googleLoginUrl = `${BASE_URL}${endpoints['gg-login']}`;
            await Linking.openURL(googleLoginUrl);
        } catch (ex) {
            console.error(ex);
            setMsg('Lỗi khi mở đăng nhập Google!');
        }
    };

    return (
        <View style = {{marginTop: 40}}>
            <ScrollView >
                <HelperText type="error" visible={msg}>
                    {msg}
                </HelperText>

                {info.map(i => (
                    <TextInput 
                    value={user[i.field]} 
                    onChangeText={t => setState(t, i.field)} 
                    style={MyStyles.m} 
                    key={i.field} 
                    label={i.label} 
                    secureTextEntry={i.secureTextEntry} 
                    right={<TextInput.Icon icon={i.icon} />}
                    />
                ))}
                <Button style={[MyStyles.mv, MyStyles.centerRow]} disabled={loading} loading={loading} onPress={login} mode="contained">Đăng nhập</Button>
                <Text style={[MyStyles.mv, MyStyles.centerRow]}>
                    Hoặc đăng nhập bằng
                </Text>      
                <TouchableOpacity style={{ alignItems: 'center' }} onPress={handleGoogleLogin}>
                    <Image
                        source={{
                            uri: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_%22G%22_logo.svg/800px-Google_%22G%22_logo.svg.png',
                        }}
                        style={[MyStyles.logo]}
                    />
                </TouchableOpacity>
                <Text style={[MyStyles.mv, MyStyles.centerRow]}>
                    Bạn chưa có tài khoản?{' '}
                    <Text 
                    style={[MyStyles.textGreen]} 
                    >
                    Đăng ký ngay
                    </Text>
                </Text>
                <Text 
                    style={[MyStyles.textGreen, MyStyles.centerRow, MyStyles.text18]} 
                    >
                        Trải nghiệm không cần đăng nhập
                    </Text>     
            </ScrollView>
        </View>
    );
}

export default Login;