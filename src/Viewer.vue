<template lang="pug">
div.viewer#app
  viewport(
    ref='viewport',
    :items='items',
    :loaded='dataLoaded',
    :currPage='currPage',
    @nav='gotoPage',
    @close='gotoThread',
    )
    scrubber-bar(
      slot='additional-ui',
      :currPage='currPage',
      :totalPages='totalPages',
      @nav='gotoPage',
      )
</template>

<script>
import axios from 'axios'

import ScrubberBar from './ScrubberBar.vue'
import Viewport from './PhotoSwipe.vue'

export default {
  name: 'viewer',
  components: { ScrubberBar, Viewport },
  data () {
    const ris = this.$root.INITIAL_STATE

    const items = new Array(ris.total_pages)

    items[ris.page.order] = {
      src: ris.page.image_url,
      w: ris.page.image_width,
      h: ris.page.image_height,
    }

    axios(ris.links.installment_url, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    }).then((response) => {
      response.data.pages.forEach((p, i) => {
        items[i] = {
          src: p.image_url,
          w: p.image_width,
          h: p.image_height,
        }
      })
      this.dataLoaded = true
    })

    return {
      items,
      thread: ris.links.installment_url,
      totalPages: ris.total_pages,
      dataLoaded: false,
    }
  },
  computed: {
    currPage () {
      return parseInt(this.$route.params.page, 10) + 1
    },
  },
  methods: {
    getPageRoute (num) {
      return num <= 0 || this.totalPages < num ? '' : {
        name: 'page',
        params: Object.assign({}, this.$route.params, { page: num - 1 }),
      }
    },
    gotoPage (num) {
      const route = this.getPageRoute(num)
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
