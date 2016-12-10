<template lang="pug">
div.viewer#app
  viewport(
    ref='viewport',
    :index='index',
    :items='items',
    :loaded='loaded',
    :thread='thread',
    :title='title',
    @nav='handleNav',
    @close='gotoThread',
    )
    scrubber-bar(
      slot='additional-ui',
      cursor='num',
      :index='index',
      :items='items',
      :thread='thread',
      :total='total',
      @nav='handleNav',
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

const BUTTONS = [{
  name: 'next',
  text: 'Next Installment',
}, {
  name: 'parent',
  text: 'Back to Library',
}]

function jumpBtn (link, text) {
  return link ? `<a href="${link}" class="button">${text}</a>` : ''
}

function insertNextSlide (items, links, total) {
  if (links) {
    const btns = BUTTONS.map(b => jumpBtn(links[b.name], b.text)).join('')

    if (btns) {
      const slide = {
        html: `
          <div class="jump slide">
            ${btns}
          </div>
          `,
      }

      if (items.length === total) {
        items.push(slide)
      } else {
        Object.assign(items[total], slide)
      }
    }
  }
}

export default {
  name: 'viewer',
  components: { ScrubberBar, Viewport },
  data () {
    return {
      items: [],
      thread: {},
      links: {},
      total: 1,
      loaded: false,
    }
  },
  computed: {
    index () {
      if (this.$route.name.endsWith('next')) {
        return this.total
      }
      return parseInt(this.$route.params.page, 10)
    },
    title () {
      return this.thread.name
    },
    routeBase () {
      const name = this.$route.name
      return name.slice(0, name.indexOf(':'))
    },
  },
  created () {
    const ris = this.$root.INITIAL_STATE
    this.total = ris.thread.num_pages

    const items = Array.from(new Array(this.total), () => ({}))
    Object.assign(items[ris.index], parsePage(ris.page))
    insertNextSlide(items, ris.links, this.total)
    this.items = items

    this.loadThread(this.getThreadRoute(this.$route))
  },
  watch: {
    $route (to, from) {
      const toThread = this.getThreadRoute(to)
      const fromThread = this.getThreadRoute(from)

      if (!_.isEqual(toThread, fromThread)) {
        this.loadThread(toThread)
      }
    },
  },
  methods: {
    getThreadRoute (route) {
      const TYPES = ['installment', 'strip']

      const type = TYPES.filter(t => route.name.includes(t))[0]
      if (type) {
        return {
          name: type,
          params: _.pick(route.params, [type]),
        }
      }
      return null
    },
    loadThread (link) {
      let href = link
      if (typeof link === 'object') {
        href = this.$router.resolve(link).href
      }
      axios(href, {
        method: 'GET',
        headers: {
          Accept: 'application/json',
        },
      }).then((response) => {
        const thread = response.data.thread
        const items = this.items

        this.thread = _.omit(thread, ['pages'])
        this.total = thread.num_pages
        this.links = response.data.links

        items.length = this.total
        thread.pages.forEach((p, i) => {
          items[i] = Object.assign(items[i] || {}, parsePage(p))
        })
        insertNextSlide(items, this.links, this.total)
        this.loaded = true
      })
      this.loaded = false
    },
    getRoute (index) {
      if (index >= 0 && index < this.total) {
        return {
          name: `${this.routeBase}:page`,
          params: Object.assign({}, this.$route.params, { page: index }),
        }
      } else if (index === this.items.length - 1) {
        return {
          name: `${this.routeBase}:next`,
          params: this.$route.params,
        }
      }
      return ''
    },
    gotoIndex (index) {
      const route = this.getRoute(index)
      if (route) {
        this.$router.push(route)
      }
    },
    handleNav (link) {
      if (typeof link === 'number') {
        this.gotoIndex(link)
      } else {
        this.$emit('nav', link)
      }
    },
    gotoThread () {
      this.$emit('nav', this.links.thread)
    },
  },
}
</script>

<style>
@import url('http://fonts.googleapis.com/css?family=Lato');
</style>

<style lang="stylus">
$btnColor = #fff
$altBtnColor = rgba(0,0,0,.8)

html
body
.viewer
  width 100%
  height 100%
  margin 0

.viewer
  font-family Lato,'Helvetica Neue',Arial,Helvetica,sans-serif

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

.jump.slide
  display flex
  flex-flow column
  align-items center
  justify-content center
  position absolute
  top 0
  left 0
  right 0
  bottom 0

  .button
    border-radius (4/16rem)
    box-shadow 0 0 0 2px $btnColor inset
    color $btnColor
    cursor pointer
    text-align center
    padding (11/16rem) 1.5rem
    margin 0 0 1.75rem

    &:hover
      background-color $btnColor
      color $altBtnColor
</style>
