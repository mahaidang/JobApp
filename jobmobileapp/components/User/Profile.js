import React, { useContext } from 'react';
import { View } from 'react-native';
import { Button } from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { MyDispatchContext } from '../../configs/MyContexts';
import MyStyles from '../../styles/MyStyles';
import { CommonActions } from '@react-navigation/native';

const Profile = () => {
  const dispatch = useContext(MyDispatchContext);
  
  const handleLogout = async () => {
    try {
      // 1. Xóa token (quan trọng nhất)
      await AsyncStorage.removeItem('token');
      console.log('Đã xóa token thành công');
      
      // 2. Sau đó dispatch action logout để cập nhật state
      dispatch({ type: 'logout' });
      console.log('Đã gọi dispatch logout');
      
      // Không cần phải điều hướng - App.js sẽ tự động điều hướng dựa vào user === null
      
    } catch (error) {
      console.error('Lỗi khi đăng xuất:', error);
    }
  };
  
  return (
    <View style={[MyStyles.center]}>
      <Button 
        mode="contained" 
        onPress={handleLogout}
        style={{ marginTop: 20 }}
      >
        Đăng xuất
      </Button>
    </View>
  );
};
 
export default Profile;