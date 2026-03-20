import { expectTypeOf, describe, test } from "vitest";
import { styled, styledHtml } from "./styled.native.js";
describe("styled.a() types", function () {
  var StyledAnchor = styled.a({
    color: "$blue10"
  });
  test("styled.a() accepts href prop", function () {
    expectTypeOf().toHaveProperty("href"), expectTypeOf().toMatchTypeOf();
  }), test("styled.a() accepts target prop", function () {
    expectTypeOf().toHaveProperty("target");
  }), test("styled.a() accepts rel prop", function () {
    expectTypeOf().toHaveProperty("rel");
  }), test("styled.a() accepts text style props", function () {
    expectTypeOf().toHaveProperty("color"), expectTypeOf().toHaveProperty("fontSize"), expectTypeOf().toHaveProperty("fontWeight"), expectTypeOf().toHaveProperty("textDecorationLine");
  });
});
describe("styled.button() types", function () {
  var StyledButton = styled.button({
    padding: "$4"
  });
  test("styled.button() accepts type prop", function () {
    expectTypeOf().toHaveProperty("type");
  }), test("styled.button() accepts disabled prop", function () {
    expectTypeOf().toHaveProperty("disabled");
  }), test("styled.button() accepts onClick prop", function () {
    expectTypeOf().toHaveProperty("onClick");
  }), test("styled.button() accepts stack style props", function () {
    expectTypeOf().toHaveProperty("padding"), expectTypeOf().toHaveProperty("backgroundColor"), expectTypeOf().toHaveProperty("borderRadius");
  });
});
describe("styled.input() types", function () {
  var StyledInput = styled.input({
    padding: "$2"
  });
  test("styled.input() accepts type prop", function () {
    expectTypeOf().toHaveProperty("type");
  }), test("styled.input() accepts placeholder prop", function () {
    expectTypeOf().toHaveProperty("placeholder");
  }), test("styled.input() accepts maxLength prop", function () {
    expectTypeOf().toHaveProperty("maxLength");
  }), test("styled.input() accepts value prop", function () {
    expectTypeOf().toHaveProperty("value");
  }), test("styled.input() accepts onChange prop", function () {
    expectTypeOf().toHaveProperty("onChange");
  });
});
describe("styled.form() types", function () {
  var StyledForm = styled.form({
    gap: "$3"
  });
  test("styled.form() accepts action prop", function () {
    expectTypeOf().toHaveProperty("action");
  }), test("styled.form() accepts method prop", function () {
    expectTypeOf().toHaveProperty("method");
  }), test("styled.form() accepts onSubmit prop", function () {
    expectTypeOf().toHaveProperty("onSubmit");
  });
});
describe("styled.label() types", function () {
  var StyledLabel = styled.label({
    fontSize: "$3"
  });
  test("styled.label() accepts htmlFor prop", function () {
    expectTypeOf().toHaveProperty("htmlFor");
  });
});
describe("styled.div() types", function () {
  var StyledDiv = styled.div({
    padding: "$4"
  });
  test("styled.div() accepts stack style props", function () {
    expectTypeOf().toHaveProperty("padding"), expectTypeOf().toHaveProperty("margin"), expectTypeOf().toHaveProperty("flex"), expectTypeOf().toHaveProperty("backgroundColor");
  });
});
describe("styled.span() types", function () {
  var StyledSpan = styled.span({
    color: "$color"
  });
  test("styled.span() accepts text style props", function () {
    expectTypeOf().toHaveProperty("color"), expectTypeOf().toHaveProperty("fontSize"), expectTypeOf().toHaveProperty("fontWeight"), expectTypeOf().toHaveProperty("lineHeight");
  });
});
describe("styled.element() with variants", function () {
  var StyledAnchorWithVariants = styled.a({
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
  test("styled.a() with variants accepts size variant", function () {
    expectTypeOf().toHaveProperty("size");
  }), test("styled.a() with variants accepts underline variant", function () {
    expectTypeOf().toHaveProperty("underline");
  }), test("styled.a() with variants still accepts href", function () {
    expectTypeOf().toHaveProperty("href");
  });
});
describe("styledHtml() function", function () {
  var StyledAnchor = styledHtml("a", {
    color: "$blue10"
  });
  test('styledHtml("a") accepts href prop', function () {
    expectTypeOf().toHaveProperty("href");
  });
});
describe("semantic HTML elements", function () {
  test("styled.nav() creates nav element component", function () {
    var StyledNav = styled.nav({
      padding: "$2"
    });
    expectTypeOf().toHaveProperty("padding");
  }), test("styled.main() creates main element component", function () {
    var StyledMain = styled.main({
      flex: 1
    });
    expectTypeOf().toHaveProperty("flex");
  }), test("styled.section() creates section element component", function () {
    var StyledSection = styled.section({
      padding: "$3"
    });
    expectTypeOf().toHaveProperty("padding");
  }), test("styled.article() creates article element component", function () {
    var StyledArticle = styled.article({
      padding: "$3"
    });
    expectTypeOf().toHaveProperty("padding");
  }), test("styled.header() creates header element component", function () {
    var StyledHeader = styled.header({
      padding: "$2"
    });
    expectTypeOf().toHaveProperty("padding");
  }), test("styled.footer() creates footer element component", function () {
    var StyledFooter = styled.footer({
      padding: "$2"
    });
    expectTypeOf().toHaveProperty("padding");
  });
});
//# sourceMappingURL=styledHtml.test-d.native.js.map
