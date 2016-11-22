import Vue from 'vue'
import VueRouter from 'vue-router'
import VueTouch from 'vue-touch'

import Viewer from './Viewer.vue'

VueTouch.config.pan = {
  threshold: 0,
}

Vue.use(VueRouter)
Vue.use(VueTouch)

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
