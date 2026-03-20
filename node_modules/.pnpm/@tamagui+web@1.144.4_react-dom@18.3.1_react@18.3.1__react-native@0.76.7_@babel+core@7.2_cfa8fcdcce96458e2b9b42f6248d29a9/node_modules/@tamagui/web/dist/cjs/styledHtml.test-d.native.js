"use strict";

var import_vitest = require("vitest"),
  import_styled = require("./styled.native.js");
(0, import_vitest.describe)("styled.a() types", function () {
  var StyledAnchor = import_styled.styled.a({
    color: "$blue10"
  });
  (0, import_vitest.test)("styled.a() accepts href prop", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("href"), (0, import_vitest.expectTypeOf)().toMatchTypeOf();
  }), (0, import_vitest.test)("styled.a() accepts target prop", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("target");
  }), (0, import_vitest.test)("styled.a() accepts rel prop", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("rel");
  }), (0, import_vitest.test)("styled.a() accepts text style props", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("color"), (0, import_vitest.expectTypeOf)().toHaveProperty("fontSize"), (0, import_vitest.expectTypeOf)().toHaveProperty("fontWeight"), (0, import_vitest.expectTypeOf)().toHaveProperty("textDecorationLine");
  });
});
(0, import_vitest.describe)("styled.button() types", function () {
  var StyledButton = import_styled.styled.button({
    padding: "$4"
  });
  (0, import_vitest.test)("styled.button() accepts type prop", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("type");
  }), (0, import_vitest.test)("styled.button() accepts disabled prop", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("disabled");
  }), (0, import_vitest.test)("styled.button() accepts onClick prop", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("onClick");
  }), (0, import_vitest.test)("styled.button() accepts stack style props", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("padding"), (0, import_vitest.expectTypeOf)().toHaveProperty("backgroundColor"), (0, import_vitest.expectTypeOf)().toHaveProperty("borderRadius");
  });
});
(0, import_vitest.describe)("styled.input() types", function () {
  var StyledInput = import_styled.styled.input({
    padding: "$2"
  });
  (0, import_vitest.test)("styled.input() accepts type prop", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("type");
  }), (0, import_vitest.test)("styled.input() accepts placeholder prop", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("placeholder");
  }), (0, import_vitest.test)("styled.input() accepts maxLength prop", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("maxLength");
  }), (0, import_vitest.test)("styled.input() accepts value prop", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("value");
  }), (0, import_vitest.test)("styled.input() accepts onChange prop", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("onChange");
  });
});
(0, import_vitest.describe)("styled.form() types", function () {
  var StyledForm = import_styled.styled.form({
    gap: "$3"
  });
  (0, import_vitest.test)("styled.form() accepts action prop", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("action");
  }), (0, import_vitest.test)("styled.form() accepts method prop", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("method");
  }), (0, import_vitest.test)("styled.form() accepts onSubmit prop", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("onSubmit");
  });
});
(0, import_vitest.describe)("styled.label() types", function () {
  var StyledLabel = import_styled.styled.label({
    fontSize: "$3"
  });
  (0, import_vitest.test)("styled.label() accepts htmlFor prop", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("htmlFor");
  });
});
(0, import_vitest.describe)("styled.div() types", function () {
  var StyledDiv = import_styled.styled.div({
    padding: "$4"
  });
  (0, import_vitest.test)("styled.div() accepts stack style props", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("padding"), (0, import_vitest.expectTypeOf)().toHaveProperty("margin"), (0, import_vitest.expectTypeOf)().toHaveProperty("flex"), (0, import_vitest.expectTypeOf)().toHaveProperty("backgroundColor");
  });
});
(0, import_vitest.describe)("styled.span() types", function () {
  var StyledSpan = import_styled.styled.span({
    color: "$color"
  });
  (0, import_vitest.test)("styled.span() accepts text style props", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("color"), (0, import_vitest.expectTypeOf)().toHaveProperty("fontSize"), (0, import_vitest.expectTypeOf)().toHaveProperty("fontWeight"), (0, import_vitest.expectTypeOf)().toHaveProperty("lineHeight");
  });
});
(0, import_vitest.describe)("styled.element() with variants", function () {
  var StyledAnchorWithVariants = import_styled.styled.a({
    color: "$blue10",
    variants: {
      size: {
        small: {
          fontSize: "$2"
        },
        large: {
          fontSize: "$6"
        }
      },
      underline: {
        true: {
          textDecorationLine: "underline"
        },
        false: {
          textDecorationLine: "none"
        }
      }
    },
    defaultVariants: {
      underline: !0
    }
  });
  (0, import_vitest.test)("styled.a() with variants accepts size variant", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("size");
  }), (0, import_vitest.test)("styled.a() with variants accepts underline variant", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("underline");
  }), (0, import_vitest.test)("styled.a() with variants still accepts href", function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("href");
  });
});
(0, import_vitest.describe)("styledHtml() function", function () {
  var StyledAnchor = (0, import_styled.styledHtml)("a", {
    color: "$blue10"
  });
  (0, import_vitest.test)('styledHtml("a") accepts href prop', function () {
    (0, import_vitest.expectTypeOf)().toHaveProperty("href");
  });
});
(0, import_vitest.describe)("semantic HTML elements", function () {
  (0, import_vitest.test)("styled.nav() creates nav element component", function () {
    var StyledNav = import_styled.styled.nav({
      padding: "$2"
    });
    (0, import_vitest.expectTypeOf)().toHaveProperty("padding");
  }), (0, import_vitest.test)("styled.main() creates main element component", function () {
    var StyledMain = import_styled.styled.main({
      flex: 1
    });
    (0, import_vitest.expectTypeOf)().toHaveProperty("flex");
  }), (0, import_vitest.test)("styled.section() creates section element component", function () {
    var StyledSection = import_styled.styled.section({
      padding: "$3"
    });
    (0, import_vitest.expectTypeOf)().toHaveProperty("padding");
  }), (0, import_vitest.test)("styled.article() creates article element component", function () {
    var StyledArticle = import_styled.styled.article({
      padding: "$3"
    });
    (0, import_vitest.expectTypeOf)().toHaveProperty("padding");
  }), (0, import_vitest.test)("styled.header() creates header element component", function () {
    var StyledHeader = import_styled.styled.header({
      padding: "$2"
    });
    (0, import_vitest.expectTypeOf)().toHaveProperty("padding");
  }), (0, import_vitest.test)("styled.footer() creates footer element component", function () {
    var StyledFooter = import_styled.styled.footer({
      padding: "$2"
    });
    (0, import_vitest.expectTypeOf)().toHaveProperty("padding");
  });
});
//# sourceMappingURL=styledHtml.test-d.native.js.map
