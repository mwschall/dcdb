import Vue from 'vue'
import VueRouter from 'vue-router'

import Viewer from './Viewer.vue'


Vue.use(VueRouter)

const routes = [
  { path: '/comics/installment/:installment/page/:page', component: Viewer, name: 'page' },
]

const router = new VueRouter({
  routes,
  mode: 'history',
})

const app = new Vue({
  router,
  template: `<router-view></router-view>`,
}).$mount('#app')
