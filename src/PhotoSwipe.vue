<template lang="pug">
div.pswp(tabindex='-1', role='dialog', ariaHidden='true', ref='pswp')
  div.pswp__bg
  div.pswp__scroll-wrap
    div.pswp__container
      div.pswp__item
      div.pswp__item
      div.pswp__item
    div.pswp__ui.pswp__ui--hidden
      div.pswp__top-bar
        div.pswp__counter
        button.pswp__button.pswp__button--close(title='Close (Esc)')
        button.pswp__button.pswp__button--fs(title='Toggle fullscreen')
        button.pswp__button.pswp__button--zoom(title='Zoom in/out')
        div.pswp__preloader
          div.pswp__preloader__icn
            div.pswp__preloader__cut
              div.pswp__preloader__donut
      div.pswp__button.pswp__button--arrow--left(title='Previous (arrow left)')
      div.pswp__button.pswp__button--arrow--right(title='Next (arrow right)')
      div.pswp__extra
        slot(name='additional-ui')
</template>

<script>
import PhotoSwipe from 'photoswipe'
import PhotoSwipeUIDefault from 'photoswipe/dist/photoswipe-ui-default'

function getPswpOptions () {
  return {
    history: false,
    loop: false,
    preload: [1, 3],

    // UI Options
    mainClass: 'pswp--minimal--dark',
    barsSize: { top: 0, bottom: 0 },
    captionEl: false,
    fullscreenEl: true,
    shareEl: false,
    bgOpacity: 1,
    closeOnScroll: false,
    tapToClose: false,
    tapToToggleControls: true,
  }
}

export default {
  name: 'viewport',
  props: ['items', 'loaded', 'currPage'],
  data () {
    return {
      gallery: undefined,
    }
  },
  methods: {
    open () {
      if (this.gallery || !this.$el) {
        return
      }

      this.gallery = new PhotoSwipe(
        this.$refs.pswp,
        PhotoSwipeUIDefault,
        this.items,
        Object.assign(getPswpOptions(), {
          index: this.currPage - 1,
        }),
      )

      this.gallery.listen('beforeChange', () => {
        const num = this.gallery.getCurrentIndex() + 1
        this.$emit('nav', num)
      })

      this.gallery.listen('close', () => {
        this.$emit('close')
      })

      this.gallery.init()
    },
  },
  watch: {
    currPage (newPage) {
      if (this.gallery) {
        const newIndex = newPage - 1
        this.gallery.goTo(newIndex)
      }
    },
    loaded () {
      const pswp = this.gallery
      pswp.invalidateCurrItems()
      pswp.updateSize(true)
      pswp.ui.update()
    },
  },
  mounted () {
    this.open()
  },
  beforeDestroy () {
    if (this.gallery) {
      this.gallery.close()
    }
  },
}
</script>

<style>
@import "~photoswipe/dist/photoswipe.css";
@import "~photoswipe/dist/default-skin/default-skin.css";
</style>
