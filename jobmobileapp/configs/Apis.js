import axios from "axios";

export const BASE_URL = 'http://10.81.47.42:8000';

export const endpoints = {

    'register': '/users/',
    'login': '/o/token/',
    'gg-login': '/accounts/google/login/',
    'current-user': '/users/me/',
}

export const authApis = (token) => {
    return axios.create({
        baseURL: BASE_URL,
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
}

export default axios.create({
    baseURL: BASE_URL
})