/* eslint no-underscore-dangle: "off" */

import Vue from 'vue'
import VueRouter from 'vue-router'
import Vue2TouchEvents from 'vue2-touch-events'

import Viewer from './Viewer.vue'

Vue.use(VueRouter)
Vue.use(Vue2TouchEvents, {
  // TODO: this no longer prevents PhotoSwipe from panning under the scrubber bar
  tapTolerance: 0,
})

const jsonNode = document.querySelector('#__INITIAL_STATE__')
const INITIAL_STATE = JSON.parse(jsonNode.textContent || '{}')

const routes = [
  { path: '/installment/:installment/page/:page', component: Viewer, name: 'installment:page' },
  { path: '/installment/:installment/next', component: Viewer, name: 'installment:next' },
  { path: '/installment/:installment', name: 'installment' },
  { path: '/strip/:strip/page/:page', component: Viewer, name: 'strip:page' },
  { path: '/strip/:strip', name: 'strip' },
]

const router = new VueRouter({
  routes,
  mode: 'history',
  base: INITIAL_STATE.base,
})

window.__APP__ = new Vue({
  router,
  // NOTE: you can NOT v-bind variables here or the router will silently fail
  template: `<router-view @nav="handleNav" />`,
  data () {
    return {
      INITIAL_STATE,
    }
  },
  methods: {
    handleNav (href) {
      let link = href
      if (href.startsWith(this.INITIAL_STATE.base)) {
        link = href.slice(this.INITIAL_STATE.base.length - 1)
      }
      const name = this.$router.resolve(link).resolved.name
      if (name && name.indexOf(':') !== -1) {
        this.$router.push(link)
      } else {
        window.location = href
      }
    },
  },
}).$mount('#app')
