<template lang="pug">
div.viewer#app
  viewport(
    ref='viewport',
    :items='items',
    :loaded='dataLoaded',
    :index='index',
    :title='title',
    @nav='gotoIndex',
    @close='gotoThread',
    )
    scrubber-bar(
      slot='additional-ui',
      cursor='num',
      :items='items',
      :index='index',
      :totalPages='totalPages',
      @nav='gotoIndex',
      )
</template>

<script>
import _ from 'lodash'
import axios from 'axios'

import ScrubberBar from './ScrubberBar.vue'
import Viewport from './PhotoSwipe.vue'

function parsePage (page) {
  return {
    number: page.number,
    src: page.image_url,
    w: page.image_width,
    h: page.image_height,
  }
}

export default {
  name: 'viewer',
  components: { ScrubberBar, Viewport },
  data () {
    const ris = this.$root.INITIAL_STATE

    const items = new Array(ris.total_pages)

    items[ris.index] = parsePage(ris.page)

    axios(ris.links.thread_url, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    }).then((response) => {
      response.data.pages.forEach((p, i) => {
        items[i] = parsePage(p)
      })
      this.dataLoaded = true
      this.info = _.omitBy(response.data, (v, k) => k === 'pages')
    })

    return {
      items,
      info: {},
      thread: ris.links.thread_url,
      totalPages: ris.total_pages,
      dataLoaded: false,
    }
  },
  computed: {
    index () {
      return parseInt(this.$route.params.page, 10)
    },
    title () {
      return this.info.name
    },
  },
  methods: {
    getRoute (index) {
      return index < 0 || this.totalPages <= index ? '' : {
        name: 'page',
        params: Object.assign({}, this.$route.params, { page: index }),
      }
    },
    gotoIndex (index) {
      const route = this.getRoute(index)
      if (route) {
        this.$router.push(route)
      }
    },
    gotoThread () {
      window.location = this.thread
    },
  },
}
</script>

<style lang="stylus">
html
body
.viewer
  width 100%
  height 100%
  margin 0

.viewer
  a
    text-decoration none

  .icon
    font-size 3rem
    color #222
    text-shadow -1px 0 #ddd, 0 1px #ddd, 1px 0 #ddd, 0 -1px #ddd
    opacity .1
    :hover > ^[1..-1]
      opacity .5

  .arrow
    position absolute
    top 0
    left 0
    right 0
    bottom 0

.arrow
  width 20%
  .icon
    position absolute
    top 50%
    margin-top -1.5rem
  .left&
    right auto
    .icon
      left 5%
  .right&
    left auto
    .icon
      right 5%
  &.disabled
    cursor default
    .icon
      visibility hidden

.close
  position absolute
  top .5rem
  left .5rem
  padding 1rem
</style>
