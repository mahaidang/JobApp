// Home.js
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import MyStyles from '../../styles/MyStyles';

const Home = () => {
    return (
        <View style={[MyStyles.container, MyStyles.center]}>
            <Text >Chào mừng đến trang chủ!</Text>
            <Text >Đây là nội dung thử nghiệm của bạn.</Text>
        </View>
    );
};

export default Home;
