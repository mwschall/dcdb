import Vue from 'vue'
import VueRouter from 'vue-router'
import VueTouch from 'vue-touch'

import Viewer from './Viewer.vue'

VueTouch.config = {
  pan: {
    threshold: 0,
  },
}

Vue.use(VueRouter)
Vue.use(VueTouch)

/* eslint no-underscore-dangle: "off" */
const INITIAL_STATE = window.window.__INITIAL_STATE__ || {}

const routes = [
  { path: '/page/:page', component: Viewer, name: 'page' },
]

const router = new VueRouter({
  routes,
  mode: 'history',
  base: INITIAL_STATE.base,
})

const app = new Vue({
  router,
  template: `<router-view></router-view>`,
  data: {
    INITIAL_STATE,
  },
}).$mount('#app')
