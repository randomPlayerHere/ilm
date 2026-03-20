import { expectTypeOf, describe, test } from "vitest";
import { styled, styledHtml } from "./styled.mjs";
describe("styled.a() types", () => {
  const StyledAnchor = styled.a({
    color: "$blue10"
  });
  test("styled.a() accepts href prop", () => {
    expectTypeOf().toHaveProperty("href"), expectTypeOf().toMatchTypeOf();
  }), test("styled.a() accepts target prop", () => {
    expectTypeOf().toHaveProperty("target");
  }), test("styled.a() accepts rel prop", () => {
    expectTypeOf().toHaveProperty("rel");
  }), test("styled.a() accepts text style props", () => {
    expectTypeOf().toHaveProperty("color"), expectTypeOf().toHaveProperty("fontSize"), expectTypeOf().toHaveProperty("fontWeight"), expectTypeOf().toHaveProperty("textDecorationLine");
  });
});
describe("styled.button() types", () => {
  const StyledButton = styled.button({
    padding: "$4"
  });
  test("styled.button() accepts type prop", () => {
    expectTypeOf().toHaveProperty("type");
  }), test("styled.button() accepts disabled prop", () => {
    expectTypeOf().toHaveProperty("disabled");
  }), test("styled.button() accepts onClick prop", () => {
    expectTypeOf().toHaveProperty("onClick");
  }), test("styled.button() accepts stack style props", () => {
    expectTypeOf().toHaveProperty("padding"), expectTypeOf().toHaveProperty("backgroundColor"), expectTypeOf().toHaveProperty("borderRadius");
  });
});
describe("styled.input() types", () => {
  const StyledInput = styled.input({
    padding: "$2"
  });
  test("styled.input() accepts type prop", () => {
    expectTypeOf().toHaveProperty("type");
  }), test("styled.input() accepts placeholder prop", () => {
    expectTypeOf().toHaveProperty("placeholder");
  }), test("styled.input() accepts maxLength prop", () => {
    expectTypeOf().toHaveProperty("maxLength");
  }), test("styled.input() accepts value prop", () => {
    expectTypeOf().toHaveProperty("value");
  }), test("styled.input() accepts onChange prop", () => {
    expectTypeOf().toHaveProperty("onChange");
  });
});
describe("styled.form() types", () => {
  const StyledForm = styled.form({
    gap: "$3"
  });
  test("styled.form() accepts action prop", () => {
    expectTypeOf().toHaveProperty("action");
  }), test("styled.form() accepts method prop", () => {
    expectTypeOf().toHaveProperty("method");
  }), test("styled.form() accepts onSubmit prop", () => {
    expectTypeOf().toHaveProperty("onSubmit");
  });
});
describe("styled.label() types", () => {
  const StyledLabel = styled.label({
    fontSize: "$3"
  });
  test("styled.label() accepts htmlFor prop", () => {
    expectTypeOf().toHaveProperty("htmlFor");
  });
});
describe("styled.div() types", () => {
  const StyledDiv = styled.div({
    padding: "$4"
  });
  test("styled.div() accepts stack style props", () => {
    expectTypeOf().toHaveProperty("padding"), expectTypeOf().toHaveProperty("margin"), expectTypeOf().toHaveProperty("flex"), expectTypeOf().toHaveProperty("backgroundColor");
  });
});
describe("styled.span() types", () => {
  const StyledSpan = styled.span({
    color: "$color"
  });
  test("styled.span() accepts text style props", () => {
    expectTypeOf().toHaveProperty("color"), expectTypeOf().toHaveProperty("fontSize"), expectTypeOf().toHaveProperty("fontWeight"), expectTypeOf().toHaveProperty("lineHeight");
  });
});
describe("styled.element() with variants", () => {
  const StyledAnchorWithVariants = styled.a({
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
  test("styled.a() with variants accepts size variant", () => {
    expectTypeOf().toHaveProperty("size");
  }), test("styled.a() with variants accepts underline variant", () => {
    expectTypeOf().toHaveProperty("underline");
  }), test("styled.a() with variants still accepts href", () => {
    expectTypeOf().toHaveProperty("href");
  });
});
describe("styledHtml() function", () => {
  const StyledAnchor = styledHtml("a", {
    color: "$blue10"
  });
  test('styledHtml("a") accepts href prop', () => {
    expectTypeOf().toHaveProperty("href");
  });
});
describe("semantic HTML elements", () => {
  test("styled.nav() creates nav element component", () => {
    const StyledNav = styled.nav({
      padding: "$2"
    });
    expectTypeOf().toHaveProperty("padding");
  }), test("styled.main() creates main element component", () => {
    const StyledMain = styled.main({
      flex: 1
    });
    expectTypeOf().toHaveProperty("flex");
  }), test("styled.section() creates section element component", () => {
    const StyledSection = styled.section({
      padding: "$3"
    });
    expectTypeOf().toHaveProperty("padding");
  }), test("styled.article() creates article element component", () => {
    const StyledArticle = styled.article({
      padding: "$3"
    });
    expectTypeOf().toHaveProperty("padding");
  }), test("styled.header() creates header element component", () => {
    const StyledHeader = styled.header({
      padding: "$2"
    });
    expectTypeOf().toHaveProperty("padding");
  }), test("styled.footer() creates footer element component", () => {
    const StyledFooter = styled.footer({
      padding: "$2"
    });
    expectTypeOf().toHaveProperty("padding");
  });
});
//# sourceMappingURL=styledHtml.test-d.mjs.map
